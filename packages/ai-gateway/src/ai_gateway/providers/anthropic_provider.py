import json
from typing import Any

import httpx

from ai_gateway.types import AnalysisResult, ProviderError


class AnthropicProvider:
    name = "anthropic"
    model = "claude-3-5-haiku-latest"

    def __init__(
        self, api_key: str, *, timeout_seconds: float = 30.0, max_tokens: int = 2048
    ) -> None:
        self._api_key = api_key
        self._timeout = timeout_seconds
        self._max_tokens = max_tokens

    async def analyze(self, prompt: str, context: dict[str, Any]) -> AnalysisResult:
        if not self._api_key:
            raise ProviderError("Anthropic API key not configured", self.name)

        system = context.get("system_prompt", "Respond in JSON only.")
        user_content = f"{prompt}\n\nContext:\n{json.dumps(context.get('payload', {}), ensure_ascii=False)}"

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self._api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "max_tokens": self._max_tokens,
                    "system": system,
                    "messages": [{"role": "user", "content": user_content}],
                },
            )
            if response.status_code != 200:
                raise ProviderError(f"Anthropic API error: {response.status_code}", self.name)

            payload = response.json()
            content = payload["content"][0]["text"]
            data = json.loads(content)
            confidence = float(data.get("confidence", 0.75))
            return AnalysisResult(
                data=data,
                provider=self.name,
                model=self.model,
                confidence=confidence,
                raw_response=content,
            )

    async def health_check(self) -> bool:
        return bool(self._api_key)
