import json
from typing import Any

import httpx

from ai_gateway.types import AnalysisResult, ProviderError


class OpenAiProvider:
    name = "openai"
    model = "gpt-4o-mini"

    def __init__(self, api_key: str, *, timeout_seconds: float = 30.0, max_tokens: int = 2048) -> None:
        self._api_key = api_key
        self._timeout = timeout_seconds
        self._max_tokens = max_tokens

    async def analyze(self, prompt: str, context: dict[str, Any]) -> AnalysisResult:
        if not self._api_key:
            raise ProviderError("OpenAI API key not configured", self.name)

        system = context.get("system_prompt", "You are a helpful assistant. Respond in JSON only.")
        user_content = f"{prompt}\n\nContext:\n{json.dumps(context.get('payload', {}), ensure_ascii=False)}"

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user_content},
                    ],
                    "max_tokens": self._max_tokens,
                    "temperature": 0.2,
                    "response_format": {"type": "json_object"},
                },
            )
            if response.status_code != 200:
                raise ProviderError(f"OpenAI API error: {response.status_code}", self.name)

            payload = response.json()
            content = payload["choices"][0]["message"]["content"]
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
