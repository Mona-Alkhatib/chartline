from __future__ import annotations

from typing import Any

from chartline.models_types import SchemaSummary, ValidationResult

_SUPPORTED_MARKS = {
    "bar", "line", "area", "point", "circle", "square", "tick", "rect",
    "rule", "text", "boxplot", "arc",
}


class Validator:
    def validate(self, spec: Any, schema: SchemaSummary) -> ValidationResult:
        if not isinstance(spec, dict):
            return ValidationResult(valid=False, error="Spec must be a JSON object.")

        mark = spec.get("mark")
        mark_type = mark.get("type") if isinstance(mark, dict) else mark
        if mark_type is None:
            return ValidationResult(valid=False, error="Spec must include a `mark`.")
        if mark_type not in _SUPPORTED_MARKS:
            return ValidationResult(valid=False, error=f"Unsupported mark: {mark_type}")

        known_fields = {c.name for t in schema.tables for c in t.columns}
        for field in self._extract_fields(spec):
            if field not in known_fields:
                return ValidationResult(
                    valid=False,
                    error=f"Field '{field}' not found in dataset. Available: {sorted(known_fields)}",
                )
        return ValidationResult(valid=True)

    def _extract_fields(self, spec: dict[str, Any]) -> list[str]:
        fields: list[str] = []
        encoding = spec.get("encoding") or {}
        for channel_val in encoding.values():
            if isinstance(channel_val, dict):
                f = channel_val.get("field")
                if isinstance(f, str):
                    fields.append(f)
        transforms = spec.get("transform") or []
        for t in transforms:
            if isinstance(t, dict):
                f = t.get("field")
                if isinstance(f, str):
                    fields.append(f)
        return fields
