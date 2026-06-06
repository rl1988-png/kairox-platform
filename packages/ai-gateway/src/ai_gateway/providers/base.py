from pathlib import Path
from typing import Any, Protocol

from ai_gateway.types import AnalysisResult


class AiProvider(Protocol):
    name: str
    model: str

    async def analyze(self, prompt: str, context: dict[str, Any]) -> AnalysisResult: ...

    async def health_check(self) -> bool: ...


def prompts_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "prompts"


def load_prompt(name: str) -> str:
    path = prompts_dir() / f"{name}.md"
    return path.read_text(encoding="utf-8")
