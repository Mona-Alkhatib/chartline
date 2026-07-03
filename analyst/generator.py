from __future__ import annotations

import json
from typing import Any

from analyst.models_types import GenerationResult, SchemaSummary, VegaLiteSpec
from analyst.router import Router
from analyst.validator import Validator

_MAX_TOKENS = 2000


class ChartGenerator:
    def __init__(
        self, router: Router, validator: Validator, client: Any, max_retries: int = 3,
    ) -> None:
        self.router = router
        self.validator = validator
        self.client = client
        self.max_retries = max_retries

    def generate_initial(self, user_ask: str, schema: SchemaSummary) -> GenerationResult:
        model = self.router.model_for("initial")
        system_blocks = self.router.system_blocks("initial")
        user_content = self._initial_user_content(user_ask, schema)
        return self._loop(model, system_blocks, user_content, schema, task="initial")

    def _loop(
        self, model: str, system_blocks: list[dict], user_content: str,
        schema: SchemaSummary, task: str,
    ) -> GenerationResult:
        messages: list[dict] = [
            {"role": "user", "content": user_content},
            {"role": "assistant", "content": "{"},
        ]
        last_error: str | None = None
        for attempt in range(self.max_retries + 1):
            response = self.client.messages.create(
                model=model, system=system_blocks, messages=messages,
                max_tokens=_MAX_TOKENS,
            )
            raw_text = self._extract_text(response)
            try:
                spec_dict = json.loads("{" + raw_text)
            except json.JSONDecodeError as e:
                last_error = f"JSON parse error: {e}"
                messages = self._retry_messages(user_content, raw_text, last_error)
                continue
            result = self.validator.validate(spec_dict, schema)
            if result.valid:
                return GenerationResult(
                    spec=VegaLiteSpec(spec=spec_dict), model_used=model, retries=attempt,
                )
            last_error = result.error or "invalid spec"
            messages = self._retry_messages(user_content, raw_text, last_error)
        raise ValueError(f"Chart generation failed after {self.max_retries + 1} attempts: {last_error}")

    def _extract_text(self, response: Any) -> str:
        for block in response.content:
            if getattr(block, "type", None) == "text":
                return block.text
        raise ValueError("No text block in response")

    def _retry_messages(self, user_content: str, prior_output: str, error: str) -> list[dict]:
        return [
            {"role": "user", "content": user_content},
            {"role": "assistant", "content": "{" + prior_output},
            {"role": "user", "content": (
                f"That spec was rejected: {error}\n\n"
                f"Return a corrected Vega-Lite JSON spec. JSON only."
            )},
            {"role": "assistant", "content": "{"},
        ]

    def _initial_user_content(self, user_ask: str, schema: SchemaSummary) -> str:
        return (
            f"Dataset schema:\n{schema.to_prompt_text()}\n\n"
            f"User request: {user_ask}\n\n"
            f"Return a Vega-Lite v5 JSON spec. JSON only, starting with {{."
        )
