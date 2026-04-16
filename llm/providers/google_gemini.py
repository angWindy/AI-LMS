"""Google Gemini provider via the official google-genai SDK."""

from google import genai
from google.genai import types

from llm.config import LLMConfig
from llm.models import ChatMessage, LLMRequest, LLMResponse
from llm.providers.base import LLMProvider


class GoogleGeminiProvider(LLMProvider):
    """Google AI Studio provider implementation."""

    def __init__(self, config: LLMConfig) -> None:
        self.config = config

    @property
    def provider_name(self) -> str:
        return "google"

    @staticmethod
    def _to_google_role(role: str) -> str:
        if role in {"assistant", "model"}:
            return "model"
        return "user"

    def _build_contents(self, messages: list[ChatMessage]) -> list[types.Content]:
        contents: list[types.Content] = []
        for message in messages:
            # Gemini expects system instructions in config.system_instruction.
            if message.role == "system":
                continue
            if not message.content.strip():
                continue
            contents.append(
                types.Content(
                    role=self._to_google_role(message.role),
                    parts=[types.Part(text=message.content)],
                )
            )
        return contents

    @staticmethod
    def _build_thinking_config(thinking_level: str | None) -> types.ThinkingConfig | None:
        if not thinking_level:
            return None
        return types.ThinkingConfig(thinking_level=thinking_level)

    def generate(self, request: LLMRequest) -> LLMResponse:
        if not self.config.google_api_key:
            raise ValueError("GOOGLE_AI_API_KEY is not configured.")

        client = genai.Client(api_key=self.config.google_api_key)
        model = self.config.model

        config_kwargs: dict = {
            "temperature": request.temperature,
            "max_output_tokens": request.max_output_tokens,
            "system_instruction": request.system_prompt,
        }

        thinking_config = self._build_thinking_config(request.thinking_level)
        if thinking_config is not None:
            config_kwargs["thinking_config"] = thinking_config

        config = types.GenerateContentConfig(**config_kwargs)

        try:
            response = client.models.generate_content(
                model=model,
                contents=self._build_contents(request.messages),
                config=config,
            )
        except Exception as exc:
            raise RuntimeError(f"Google AI Studio request failed: {exc}") from exc

        text = (response.text or "").strip()
        candidates = response.candidates or []
        finish_reason = None
        if candidates:
            finish_reason = str(getattr(candidates[0], "finish_reason", None) or "") or None

        usage_metadata = response.usage_metadata
        usage = {
            "prompt_tokens": int(getattr(usage_metadata, "prompt_token_count", 0) or 0),
            "completion_tokens": int(
                getattr(usage_metadata, "candidates_token_count", 0) or 0
            ),
            "total_tokens": int(getattr(usage_metadata, "total_token_count", 0) or 0),
        }

        return LLMResponse(
            text=text,
            provider=self.provider_name,
            model=model,
            finish_reason=finish_reason,
            usage=usage,
            raw=response.model_dump(),
        )
