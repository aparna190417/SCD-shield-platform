from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status

from shield.ingress.diagnostic_service import DiagnosticService
from shield.ingress.llm_adapter import FakeLLMAdapter
from shield.ingress.schemas import DiagnosticResult, Incident

VALID_DIAGNOSTIC_OUTPUT = """
{
    "incident_id": "INC-001",
    "failure_family": "interconnect",
    "affected_entity": "node-a",
    "primary_hypothesis": "NVLink degradation",
    "alternative_hypotheses": [
        "Transient communication fault"
    ],
    "supporting_evidence": [
        "link_errors=42"
    ],
    "contradicting_evidence": [],
    "missing_evidence": [
        "NVLink health counters"
    ],
    "confidence": 0.82,
    "recommended_action": "Collect NVLink health counters"
}
"""


class ServiceContainer:
    """Manages application-level singleton dependencies."""

    def __init__(self) -> None:
        self.adapter = FakeLLMAdapter(VALID_DIAGNOSTIC_OUTPUT)
        self.diagnostic_service = DiagnosticService(llm_adapter=self.adapter)


container = ServiceContainer()


def get_diagnostic_service() -> DiagnosticService:
    """FastAPI Dependency Provider for DiagnosticService."""
    return container.diagnostic_service


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Startup: Initialize connections, load caches, verify LLM adapters
    yield
    # Shutdown: Clean up sockets, thread pools, open sessions


def create_app() -> FastAPI:
    app = FastAPI(
        title="SCD-SHIELD API",
        version="1.0.0",
        description=(
            "Autonomous Supercomputer Cluster Diagnostics Engine.\n\n"
            "Provides automated root-cause analysis, failure categorization, "
            "and mitigation steps using high-throughput LLM reasoning."
        ),
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_tags=[
            {"name": "System", "description": "Liveness & telemetry endpoints."},
            {
                "name": "Diagnostics",
                "description": "Cluster incident analysis & inference operations.",
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
        description="Ingests telemetry for an active incident and returns structured root-cause hypotheses.",
        response_model=DiagnosticResult,
        status_code=status.HTTP_200_OK,
        responses={
            status.HTTP_422_UNPROCESSABLE_CONTENT: {
                "description": "Validation or parser failure in diagnostic pipeline"
            },
            status.HTTP_500_INTERNAL_SERVER_ERROR: {
                "description": "Internal diagnostic engine failure"
            },
        },
    )
    def run_diagnostics(
        incident: Incident,
        service: Annotated[DiagnosticService, Depends(get_diagnostic_service)],
    ) -> DiagnosticResult:
        try:
            return service.diagnose(incident)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"error": "DiagnosticValidationError", "message": str(exc)},
            ) from exc
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"error": "DiagnosticExecutionError", "message": "Failed to evaluate incident."},
            ) from exc

    return app


app = create_app()