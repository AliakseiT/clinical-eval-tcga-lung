#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Extract the input contract from a REAL model (gemini-2.5-flash) on TCGA-LUAD.

Runs the `gemini_contract` battery (ablation + format) with a pinned,
reference-aware lite judge, so the information-value curve reflects a real
model's real behaviour: withhold the pathology report and the model can no
longer state the diagnosis, etc. Requires GEMINI_API_KEY.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

from harness.execute import run_battery
from harness.judge.llm import GradingConfig, LLMJudge
from harness.models.sut import SUTBinding
from harness.packio.loader import load_pack
from harness.store.runstore import RunStore

ROOT = Path(__file__).parent
GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
JUDGE_MODEL = "gemini-flash-lite-latest"  # fast, non-thinking; different from the SUT


def main() -> int:
    if not os.environ.get("GEMINI_API_KEY"):
        print("Set GEMINI_API_KEY first.")
        return 1
    pack = load_pack(ROOT / "pack")
    store = RunStore(ROOT / "runs")
    judge = LLMJudge(
        SUTBinding(model_id=JUDGE_MODEL, model_version=JUDGE_MODEL,
                   endpoint=GEMINI_ENDPOINT, api_key_env="GEMINI_API_KEY"),
        GradingConfig(include_document=True, include_reference=True),
    )
    now = lambda: datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    print("Running gemini_contract (gemini-2.5-flash, ablation) ...")
    r = run_battery(pack, "gemini_contract", store, seed=1, now=now, judge=judge)[0]
    print(f"\nrun={r.run_id} units={r.n_units} acceptance="
          f"{'PASS' if r.report['acceptance']['overall_pass'] else 'FAIL'}")
    print("\n=== INPUT CONTRACT on gemini-2.5-flash (real model, real data) ===")
    for e in r.contract["elements"]:
        iv = e["information_value"]
        print(f"  {e['name']:20} measured={e['measured']!s:5} "
              f"information_value={'—' if iv is None else round(iv, 3)}")
    print("  minimal sufficient set:", r.contract["minimal_sufficient_set_candidate"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
