from typing import Any, Optional
from groq import AsyncGroq
from backend.core.config import settings
from backend.core.ai.providers.base import BaseLLMProvider


class GroqProvider(BaseLLMProvider):
    """Concrete implementation of BaseLLMProvider wrapping Groq Cloud APIs."""

    def __init__(self):
        self.client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        self.model = settings.GROQ_MODEL

    async def generate_completion_async(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        response_format: Optional[Any] = None
    ) -> Optional[str]:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            # Check if structured JSON output format is requested
            extra_params = {}
            if response_format and response_format.get("type") == "json_object":
                extra_params["response_format"] = {"type": "json_object"}

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.1,
                max_tokens=1024,
                **extra_params
            )
            return response.choices[0].message.content
        except Exception as e:
            # Fall back to console logs
            print(f"[GroqProvider] API Error: {e}")
            return None
