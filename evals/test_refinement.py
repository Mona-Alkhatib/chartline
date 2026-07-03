import json
import os
from pathlib import Path

import pytest
from anthropic import Anthropic
from dotenv import load_dotenv

from analyst.generator import ChartGenerator
from analyst.models_types import VegaLiteSpec
from analyst.router import Router
from analyst.validator import Validator

load_dotenv()

_TRIPLES_PATH = Path(__file__).parent / "fixtures" / "charts" / "refinement_triples.json"
_PASS_THRESHOLD = 0.85


def _load_triples() -> list[dict]:
    return json.loads(_TRIPLES_PATH.read_text())


def _get_by_path(obj: dict, path: str):
    cur = obj
    for part in path.split("."):
        if not isinstance(cur, dict):
            return None
        cur = cur.get(part)
    return cur


def _assertion_passes(spec: dict, assertion: dict) -> bool:
    kind = assertion["kind"]
    match kind:
        case "path_equals":
            return _get_by_path(spec, assertion["path"]) == assertion["value"]
        case "path_exists":
            return _get_by_path(spec, assertion["path"]) is not None
        case "mark_type":
            mark = spec.get("mark")
            mt = mark.get("type") if isinstance(mark, dict) else mark
            return mt == assertion["value"]
        case "title_equals":
            title = spec.get("title")
            if isinstance(title, dict):
                title = title.get("text")
            return title == assertion["value"]
    return False


@pytest.mark.llm_eval
@pytest.mark.skipif(
    os.environ.get("CHARTLINE_RUN_LLM_EVALS") != "1",
    reason="Set CHARTLINE_RUN_LLM_EVALS=1 to run live Anthropic evals.",
)
def test_refinement_correctness(sales_schema):
    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    generator = ChartGenerator(Router(), Validator(), client)
    triples = _load_triples()
    passes = 0
    failures: list[dict] = []
    for triple in triples:
        previous = VegaLiteSpec(spec=triple["starting_spec"])
        try:
            result = generator.refine(triple["refinement_ask"], previous, sales_schema)
        except Exception as e:
            failures.append({"id": triple["id"], "error": str(e)})
            continue
        if _assertion_passes(result.spec.spec, triple["assertion"]):
            passes += 1
        else:
            failures.append({"id": triple["id"], "got": result.spec.spec, "want": triple["assertion"]})
    rate = passes / len(triples)
    print(f"\nLayer 2 pass rate: {rate:.2%} ({passes}/{len(triples)})")
    for f in failures:
        print(f"  FAIL {f['id']}: {f}")
    assert rate >= _PASS_THRESHOLD, f"Layer 2 pass rate {rate:.2%} below threshold {_PASS_THRESHOLD:.0%}"
