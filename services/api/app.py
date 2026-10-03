from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from shield.config.logging import configure_logging_from_settings
from shield.config.settings import Settings, get_settings
from shield.context.builder import IncidentContextBuilder
from shield.ingress.diagnostic_service import DiagnosticService
from shield.ingress.llm_factory import create_llm_adapter
from shield.ingress.schemas import DiagnosticResult, Incident
from shield.orchestration.orchestrator import DiagnosticOrchestrator


class APIErrorResponse(BaseModel):
    """Structured API error response."""

    model_config = ConfigDict(extra="forbid")

    error: str = Field(min_length=1)
    message: str = Field(min_length=1)
    incident_id: str | None = None


class WorkflowDecisionResponse(BaseModel):
    """Governance decision returned by the workflow API."""

    model_config = ConfigDict(extra="forbid")

    incident_id: str = Field(min_length=1)
    status: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str = Field(min_length=1)
    recommended_action: str = Field(min_length=1)


class WorkflowActionResponse(BaseModel):
    """Controlled repair execution outcome."""

    model_config = ConfigDict(extra="forbid")

    incident_id: str = Field(min_length=1)
    status: str = Field(min_length=1)
    action: str = Field(min_length=1)
    message: str = Field(min_length=1)


class DiagnosticWorkflowResponse(BaseModel):
    """Complete diagnostic, governance, and repair workflow response."""

    model_config = ConfigDict(extra="forbid")

    diagnostic: DiagnosticResult
    decision: WorkflowDecisionResponse
    action: WorkflowActionResponse


class ServiceContainer:
    """Manages application-level singleton dependencies."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

        self.adapter = create_llm_adapter(self.settings)

        self.diagnostic_service = DiagnosticService(
            llm_adapter=self.adapter,
        )

        self.context_builder = IncidentContextBuilder()

        self.orchestrator = DiagnosticOrchestrator(
            self.diagnostic_service,
            context_builder=self.context_builder.build,
        )


# Default application container.
container = ServiceContainer()


def get_diagnostic_service() -> DiagnosticService:
    """FastAPI dependency provider for DiagnosticService."""

    return container.diagnostic_service


def get_diagnostic_orchestrator() -> DiagnosticOrchestrator:
    """FastAPI dependency provider for DiagnosticOrchestrator."""

    return container.orchestrator


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage application startup and shutdown."""

    yield


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure the FastAPI application."""

    global container

    if settings is not None:
        container = ServiceContainer(settings)

    configure_logging_from_settings(container.settings)

    app = FastAPI(
        title="SCD-SHIELD API",
        version="1.0.0",
        description=(
            "Autonomous Supercomputer Cluster Diagnostics Engine.\n\n"
            "Provides automated root-cause analysis, failure "
            "categorization, and mitigation steps using "
            "high-throughput LLM reasoning."
        ),
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_tags=[
            {
                "name": "System",
                "description": "Liveness & telemetry endpoints.",
            },
            {
                "name": "Diagnostics",
                "description": (
                    "Cluster incident analysis & inference operations."
                ),
            },
        ],
    )

    @app.get(
        "/health",
        tags=["System"],
        summary="Service Liveness Probe",
        status_code=status.HTTP_200_OK,
        response_model=dict[str, str],
    )
    def health_check() -> dict[str, str]:
        return {
            "status": "healthy",
            "service": "scd-shield",
            "version": "1.0.0",
        }

    @app.post(
        "/diagnose",
        tags=["Diagnostics"],
        summary="Analyze Supercomputer Incident",
        description=(
            "Ingests telemetry for an active incident and returns "
            "structured root-cause hypotheses."
        ),
        response_model=DiagnosticResult,
        status_code=status.HTTP_200_OK,
        responses={
            status.HTTP_422_UNPROCESSABLE_CONTENT: {
                "description": (
                    "Validation or parser failure in diagnostic pipeline"
                ),
                "model": APIErrorResponse,
            },
            status.HTTP_500_INTERNAL_SERVER_ERROR: {
                "description": "Internal diagnostic engine failure",
                "model": APIErrorResponse,
            },
        },
    )
    def run_diagnostics(
        incident: Incident,
        service: Annotated[
            DiagnosticService,
            Depends(get_diagnostic_service),
        ],
    ) -> DiagnosticResult:
        try:
            return service.diagnose(incident)

        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail={
                    "error": "DiagnosticValidationError",
                    "message": str(exc),
                    "incident_id": incident.incident_id,
                },
            ) from exc

        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": "DiagnosticExecutionError",
                    "message": "Failed to evaluate incident.",
                    "incident_id": incident.incident_id,
                },
            ) from exc

    @app.post(
        "/diagnose/workflow",
        tags=["Diagnostics"],
        summary="Run Complete Diagnostic Workflow",
        description=(
            "Runs incident diagnosis, governance evaluation, "
            "and the controlled repair execution boundary."
        ),
        response_model=DiagnosticWorkflowResponse,
        status_code=status.HTTP_200_OK,
        responses={
            status.HTTP_422_UNPROCESSABLE_CONTENT: {
                "description": "Diagnostic validation failure",
                "model": APIErrorResponse,
            },
            status.HTTP_500_INTERNAL_SERVER_ERROR: {
                "description": "Internal diagnostic workflow failure",
                "model": APIErrorResponse,
            },
        },
    )
    def run_diagnostic_workflow(
        incident: Incident,
        orchestrator: Annotated[
            DiagnosticOrchestrator,
            Depends(get_diagnostic_orchestrator),
        ],
    ) -> DiagnosticWorkflowResponse:
        try:
            workflow = orchestrator.run(incident)

            return DiagnosticWorkflowResponse(
                diagnostic=workflow.diagnostic,
                decision=WorkflowDecisionResponse(
                    incident_id=workflow.decision.incident_id,
                    status=workflow.decision.status,
                    confidence=workflow.decision.confidence,
                    reason=workflow.decision.reason,
                    recommended_action=(
                        workflow.decision.recommended_action
                    ),
                ),
                action=WorkflowActionResponse(
                    incident_id=workflow.action.incident_id,
                    status=workflow.action.status,
                    action=workflow.action.action,
                    message=workflow.action.message,
                ),
            )

        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail={
                    "error": "DiagnosticValidationError",
                    "message": str(exc),
                    "incident_id": incident.incident_id,
                },
            ) from exc

        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": "DiagnosticExecutionError",
                    "message": (
                        "Failed to execute diagnostic workflow."
                    ),
                    "incident_id": incident.incident_id,
                },
            ) from exc

    return app


app = create_app()