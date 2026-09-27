from typing import Any

from openai import APIStatusError, OpenAI, RateLimitError

from shield.ingress.llm_adapter import LLMRequest


class OpenAIAdapter:
    """LLM adapter backed by the OpenAI API."""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        client: Any | None = None,
    ) -> None:
        if not api_key:
            raise ValueError("OpenAI API key is required")

        self.model = model
        self.client = client or OpenAI(api_key=api_key)

    def generate(self, request: LLMRequest) -> str:
        """Generate a response using the configured OpenAI model."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": request.prompt.system,
                    },
                    {
                        "role": "developer",
                        "content": request.prompt.developer,
                    },
                    {
                        "role": "user",
                        "content": request.prompt.user,
                    },
                ],
            )
        except RateLimitError as exc:
            raise RuntimeError(
                "OpenAI rate limit or quota exceeded."
            ) from exc
        except APIStatusError as exc:
            raise RuntimeError(
                "OpenAI API request failed."
            ) from exc

        content = response.choices[0].message.content

        if not content:
            raise ValueError("LLM returned an empty response")

        return content