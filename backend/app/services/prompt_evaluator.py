"""Deterministic prompt evaluators. Never executes student text as code or calls an LLM."""

from __future__ import annotations

import json
import re
from typing import Any

from app.core.config import settings

RUBRIC_KEYS = (
    "task_accuracy",
    "format_compliance",
    "robustness",
    "instruction_following",
    "safety",
    "efficiency",
)

DEFAULT_WEIGHTS = {
    "task_accuracy": 30,
    "format_compliance": 20,
    "robustness": 15,
    "instruction_following": 15,
    "safety": 10,
    "efficiency": 10,
}


def render_prompt(template: str, variables: dict[str, Any] | None) -> str:
    rendered = template
    for key, value in (variables or {}).items():
        rendered = rendered.replace("{{" + str(key) + "}}", str(value))
    return rendered


def extract_json_object(text: str) -> Any | None:
    decoder = json.JSONDecoder()
    start = text.find("{")
    while start >= 0:
        try:
            obj, _end = decoder.raw_decode(text[start:])
            if isinstance(obj, dict):
                return obj
        except json.JSONDecodeError:
            pass
        start = text.find("{", start + 1)
    return None


def _validate_simple_schema(instance: Any, schema: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if schema.get("type") == "object" and not isinstance(instance, dict):
        return ["Expected a JSON object"]
    if not isinstance(instance, dict):
        return errors
    required = schema.get("required") or []
    for key in required:
        if key not in instance:
            errors.append(f"Missing required field: {key}")
    props = schema.get("properties") or {}
    extra_policy = schema.get("additionalProperties", True)
    if extra_policy is False:
        for key in instance:
            if key not in props:
                errors.append(f"Unexpected field: {key}")
    for key, spec in props.items():
        if key not in instance:
            continue
        value = instance[key]
        expected_type = spec.get("type")
        type_map = {"string": str, "number": (int, float), "integer": int, "boolean": bool, "object": dict, "array": list}
        py_type = type_map.get(expected_type)
        if py_type and not isinstance(value, py_type):
            if not (expected_type == "number" and isinstance(value, int)):
                errors.append(f"Field {key} should be {expected_type}")
        if "enum" in spec and value not in spec["enum"]:
            errors.append(f"Field {key} must be one of {spec['enum']}")
        if value is None and spec.get("nullable") is False:
            errors.append(f"Field {key} cannot be null")
    return errors


def _target_text(check: dict[str, Any], prompt: str, rendered: str) -> str:
    target = check.get("target", "prompt")
    if target == "rendered":
        return rendered
    return prompt


def run_check(check: dict[str, Any], *, prompt: str, rendered: str, variables: dict[str, Any]) -> tuple[bool, str]:
    ctype = (check.get("type") or "").strip().lower()
    text = _target_text(check, prompt, rendered)
    lowered = text.lower()

    if ctype in {"contains", "keyword_coverage"}:
        values = check.get("values") or ([check["value"]] if check.get("value") is not None else [])
        missing = [v for v in values if str(v).lower() not in lowered]
        return (not missing, "Contains required text" if not missing else f"Missing: {', '.join(missing)}")

    if ctype in {"not_contains", "forbidden", "forbidden_fields"}:
        values = check.get("values") or ([check["value"]] if check.get("value") is not None else [])
        hits = [v for v in values if str(v).lower() in lowered]
        return (not hits, "No forbidden text" if not hits else "Prompt includes disallowed wording")

    if ctype == "exact_match":
        expected = str(check.get("value") or "")
        ok = text.strip() == expected.strip()
        return ok, "Exact match" if ok else "Did not match expected text"

    if ctype == "regex":
        pattern = str(check.get("pattern") or check.get("value") or "")
        if len(pattern) > settings.prompt_max_regex_length:
            return False, "Regex pattern too long"
        try:
            ok = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL) is not None
        except re.error:
            return False, "Invalid regex in challenge config"
        return ok, "Pattern matched" if ok else "Required pattern not found"

    if ctype == "variable_used":
        names = check.get("names") or check.get("values") or []
        missing = [n for n in names if "{{" + n + "}}" not in prompt]
        return (not missing, "Uses template variables" if not missing else f"Add variables: {', '.join(missing)}")

    if ctype == "json_validity":
        obj = extract_json_object(text)
        return (obj is not None, "Contains valid JSON" if obj is not None else "No valid JSON object found")

    if ctype in {"json_schema", "required_fields", "allowed_value"}:
        schema = check.get("schema") or {}
        obj = extract_json_object(text)
        if obj is None:
            return False, "No JSON object to validate"
        errors = _validate_simple_schema(obj, schema)
        return (not errors, "JSON schema ok" if not errors else errors[0])

    if ctype == "classification_label":
        labels = [str(v).lower() for v in (check.get("labels") or check.get("values") or [])]
        ok = all(label in lowered for label in labels)
        return ok, "Lists required labels" if ok else "Prompt must name the allowed labels"

    if ctype == "format_compliance":
        markers = check.get("values") or ["json"]
        ok = all(str(m).lower() in lowered for m in markers)
        return ok, "Format instructions present" if ok else "Add format instructions"

    if ctype == "max_length":
        limit = int(check.get("value") or settings.prompt_max_chars)
        ok = len(prompt) <= limit
        return ok, "Within length limit" if ok else "Prompt exceeds length limit"

    if ctype == "efficiency":
        limit = int(check.get("value") or 1500)
        ok = len(prompt) <= limit
        return ok, "Reasonably concise" if ok else "Trim the prompt for efficiency"

    return False, f"Unknown check type: {ctype}"


class PromptEvaluator:
    """Runs configured deterministic checks. Student text is never executed."""

    def evaluate_case(
        self,
        *,
        prompt: str,
        case_variables: dict[str, Any],
        evaluation_config: dict[str, Any],
        expected_schema: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        rendered = render_prompt(prompt, case_variables)
        checks = list(evaluation_config.get("checks") or [])
        if expected_schema:
            checks.append({"type": "json_schema", "target": "prompt", "schema": expected_schema, "rubric": "format_compliance"})
        if not checks:
            return {"passed": False, "score": 0, "feedback": "Challenge has no evaluators", "check_results": []}

        results = []
        weighted_pass = 0.0
        weighted_total = 0.0
        for check in checks:
            weight = float(check.get("weight") or 1)
            ok, message = run_check(check, prompt=prompt, rendered=rendered, variables=case_variables)
            rubric = check.get("rubric") or "task_accuracy"
            results.append({"type": check.get("type"), "passed": ok, "message": message, "rubric": rubric, "weight": weight})
            weighted_total += weight
            if ok:
                weighted_pass += weight
        score = round(100.0 * weighted_pass / weighted_total, 2) if weighted_total else 0
        passed = score >= float(evaluation_config.get("pass_score") or 100)
        if evaluation_config.get("require_all", True):
            passed = all(r["passed"] for r in results)
            score = 100.0 if passed else score
        failed = [r["message"] for r in results if not r["passed"]]
        feedback = "All checks passed." if passed else "; ".join(failed[:4])
        return {"passed": passed, "score": score, "feedback": feedback, "check_results": results}

    def aggregate(
        self,
        case_rows: list[dict[str, Any]],
        rubric_weights: dict[str, Any] | None,
    ) -> tuple[float, dict[str, float], str]:
        weights = {k: float(rubric_weights.get(k, DEFAULT_WEIGHTS[k])) for k in RUBRIC_KEYS} if rubric_weights else dict(DEFAULT_WEIGHTS)
        total_w = sum(weights.values()) or 1
        dim_scores: dict[str, list[float]] = {k: [] for k in RUBRIC_KEYS}
        case_weight_total = 0.0
        case_weight_score = 0.0
        for row in case_rows:
            w = float(row.get("weight") or 1)
            case_weight_total += w
            case_weight_score += w * float(row.get("score") or 0)
            by_rubric: dict[str, list[bool]] = {}
            for check in row.get("check_results") or []:
                by_rubric.setdefault(check.get("rubric") or "task_accuracy", []).append(bool(check.get("passed")))
            for key, flags in by_rubric.items():
                if key in dim_scores:
                    dim_scores[key].append(100.0 if all(flags) else (100.0 * sum(flags) / len(flags)))
        overall = round(case_weight_score / case_weight_total, 2) if case_weight_total else 0
        breakdown = {
            key: round(sum(vals) / len(vals), 2) if vals else 0.0 for key, vals in dim_scores.items()
        }
        weighted = round(sum(breakdown[k] * weights[k] for k in RUBRIC_KEYS) / total_w, 2)
        final = round((overall + weighted) / 2, 2)
        feedback = "Deterministic practice score — not a scientific LLM eval."
        return final, breakdown, feedback


def validate_challenge_config(challenge: dict[str, Any], cases: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    public = [c for c in cases if not c.get("is_hidden")]
    if not public:
        errors.append("At least one public case is required")
    if len(cases) > settings.prompt_max_cases:
        errors.append("Too many cases")
    weights = challenge.get("rubric_weights") or {}
    if weights:
        if any(float(v) < 0 for v in weights.values()):
            errors.append("Rubric weights must be non-negative")
        if sum(float(v) for v in weights.values()) <= 0:
            errors.append("Rubric weights must sum to a positive number")
    for idx, case in enumerate(cases):
        config = case.get("evaluation_config") or {}
        checks = config.get("checks") or []
        if not checks and not case.get("expected_schema"):
            errors.append(f"Case {idx + 1} needs evaluation checks")
        for check in checks:
            if check.get("type") == "regex":
                pattern = str(check.get("pattern") or check.get("value") or "")
                if len(pattern) > settings.prompt_max_regex_length:
                    errors.append(f"Case {idx + 1} regex is too long")
                try:
                    re.compile(pattern)
                except re.error:
                    errors.append(f"Case {idx + 1} regex does not compile")
            if check.get("type") == "json_schema" and not isinstance(check.get("schema"), dict):
                errors.append(f"Case {idx + 1} json_schema needs a schema object")
        schema = case.get("expected_schema")
        if schema is not None and not isinstance(schema, dict):
            errors.append(f"Case {idx + 1} expected_schema must be an object")
    return errors
