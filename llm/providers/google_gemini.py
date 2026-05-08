"""Google Gemini provider via the official google-genai SDK."""

import logging
import time

from google import genai
from google.genai import types

from llm.config import LLMConfig
from llm.models import ChatMessage, ImageInput, LLMRequest, LLMResponse
from llm.providers.base import LLMProvider


logger = logging.getLogger(__name__)


class GoogleGeminiProvider(LLMProvider):
    """Google AI Studio provider implementation."""

    def __init__(self, config: LLMConfig) -> None:
        self.config = config

    @property
    def provider_name(self) -> str:
        return "google"

    @property
    def supports_json_mode(self) -> bool:
        """Gemini models support JSON mode; gemma-* models do not."""
        return self.config.model.lower().startswith("gemini")

    @staticmethod
    def _to_google_role(role: str) -> str:
        if role in {"assistant", "model"}:
            return "model"
        return "user"

    def _build_contents(
        self,
        messages: list[ChatMessage],
        images: list[ImageInput] | None = None,
    ) -> list[types.Content]:
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

        image_parts = [
            types.Part.from_bytes(data=image.data, mime_type=image.mime_type)
            for image in (images or [])
            if image.data
        ]
        if image_parts:
            # Place images in the latest user turn so the model sees visual context
            # immediately before answering the user's current question.
            target_index = next(
                (i for i in range(len(contents) - 1, -1, -1) if contents[i].role == "user"),
                None,
            )
            if target_index is None:
                contents.append(types.Content(role="user", parts=image_parts))
            else:
                existing_parts = list(contents[target_index].parts or [])
                contents[target_index] = types.Content(
                    role="user",
                    parts=[*image_parts, *existing_parts],
                )

        return contents

    @staticmethod
    def _build_thinking_config(thinking_level: str | None) -> types.ThinkingConfig | None:
        if not thinking_level:
            return None
        return types.ThinkingConfig(thinking_level=thinking_level)

    def generate(self, request: LLMRequest) -> LLMResponse:
        if not self.config.google_api_key:
            logger.error("[Error][Gemini] GOOGLE_AI_API_KEY is not configured")
            raise ValueError("GOOGLE_AI_API_KEY is not configured.")

        timeout_seconds = request.metadata.get("request_timeout_seconds")
        if timeout_seconds is None:
            timeout_seconds = self.config.request_timeout_seconds

        http_options = None
        if timeout_seconds is not None:
            safe_seconds = max(float(timeout_seconds), 10.0)
            timeout_ms = int(safe_seconds * 1000)
            http_options = types.HttpOptions(timeout=timeout_ms)

        client = genai.Client(api_key=self.config.google_api_key, http_options=http_options)
        model = self.config.model

        config_kwargs: dict = {
            "temperature": request.temperature,
            "system_instruction": request.system_prompt,
        }
        if request.max_output_tokens is not None:
            config_kwargs["max_output_tokens"] = request.max_output_tokens

        response_mime_type = request.metadata.get("response_mime_type")
        if response_mime_type:
            config_kwargs["response_mime_type"] = response_mime_type

        thinking_config = None
        if model.lower().startswith("gemini"):
            thinking_config = self._build_thinking_config(request.thinking_level)
        elif request.thinking_level:
            logger.debug(
                "[Debug][Gemini] Ignoring thinking_level for model=%s (unsupported)",
                model,
            )
        if thinking_config is not None:
            config_kwargs["thinking_config"] = thinking_config

        config = types.GenerateContentConfig(**config_kwargs)
        contents = self._build_contents(request.messages, request.images)

        logger.debug(
            "[Debug][Gemini] Sending request model=%s messages=%s images=%s temperature=%s max_output_tokens=%s thinking_level=%s response_mime_type=%s",
            model,
            len(request.messages),
            len(request.images),
            request.temperature,
            request.max_output_tokens,
            request.thinking_level,
            response_mime_type,
        )

        start_time = time.monotonic()
        try:
            response = client.models.generate_content(
                model=model,
                contents=contents,
                config=config,
            )
        except Exception as exc:
            elapsed_ms = int((time.monotonic() - start_time) * 1000)
            logger.exception(
                "[Error][Gemini] Request failed model=%s messages=%s images=%s temperature=%s max_output_tokens=%s thinking_level=%s duration_ms=%s error=%s",
                model,
                len(request.messages),
                len(request.images),
                request.temperature,
                request.max_output_tokens,
                request.thinking_level,
                elapsed_ms,
                exc,
            )
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

        elapsed_ms = int((time.monotonic() - start_time) * 1000)
        logger.info(
            "[Success][Gemini] Response model=%s finish_reason=%s prompt_tokens=%s completion_tokens=%s total_tokens=%s duration_ms=%s has_image_input=%s image_input_count=%s",
            model,
            finish_reason,
            usage["prompt_tokens"],
            usage["completion_tokens"],
            usage["total_tokens"],
            elapsed_ms,
            len(request.images or []) > 0,
            len(request.images or []),
        )

        return LLMResponse(
            text=text,
            provider=self.provider_name,
            model=model,
            finish_reason=finish_reason,
            usage=usage,
            raw=response.model_dump(),
        )
