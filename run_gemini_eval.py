#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Real-model demo: validate + compare two Gemini models on the TCGA-LUAD pack.

Runs `gemini_compare` (gemini-2.5-pro vs gemini-2.5-flash) via Google's
OpenAI-compatible endpoint, grades the free-text output with a pinned,
reference-aware LLM judge, and produces:
  1. per-model validation scores,
  2. a RegressionDiff between the two models (a model swap is a CHANGE event,
     not a temporal trend) + a QMS change request,
  3. an explicitly-labeled monitoring PROJECTION (modeled from the weaker model's
     measured error — NOT clinician telemetry).

Requires GEMINI_API_KEY in the environment. Sending TCGA (public, de-identified)
to the public Gemini API is fine; real patient data would need Vertex/BAA or
local inference.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from harness.diff import diff_runs
from harness.execute import run_battery
from harness.judge.llm import GradingConfig, LLMJudge
from harness.models.sut import SUTBinding
from harness.packio.loader import load_pack
from harness.qms.mappers import build_change_request
from harness.store.runstore import RunStore

ROOT = Path(__file__).parent
GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
# Pinned judge. NOTE: Gemini judging Gemini is same-family bias — for production
# use a different-family judge, or human calibration (which is what kappa is for).
JUDGE_MODEL = "gemini-flash-lite-latest"


def _clock():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


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

    print(f"Running gemini_compare (judge={JUDGE_MODEL}, reference-aware) ...")
    results = run_battery(pack, "gemini_compare", store, seed=1, now=_clock, judge=judge)
    by_sut = {r.sut_id: r for r in results}

    print("\n=== per-model validation (baseline, real TCGA-LUAD) ===")
    for sut_id, r in sorted(by_sut.items()):
        ms = r.report["summary"]["mean_score"]["mean"]
        errs = r.report["summary"].get("judge_errors", 0)
        print(f"  {sut_id:24} mean_score={ms:.3f}  judge_errors={errs}  "
              f"acceptance={'PASS' if r.report['acceptance']['overall_pass'] else 'FAIL'}")

    strong, weak = by_sut["gemini-2.5-pro"], by_sut["gemini-2.5-flash"]
    diff = diff_runs(store, strong.run_id, weak.run_id)
    agg = diff["aggregate"]
    print("\n=== RegressionDiff: gemini-2.5-pro -> gemini-2.5-flash (a model change) ===")
    print(f"  mean score {agg['mean_score_baseline']:.3f} -> {agg['mean_score_candidate']:.3f} "
          f"(delta {agg['delta']:+.3f}, {'significant' if agg['significant'] else 'not significant'})")
    print(f"  item regressions={diff['n_regressions']} improvements={diff['n_improvements']}")
    for d in diff["item_deltas"][:12]:
        if d["delta"] < 0:
            print(f"    regressed: {d['case_id']} / {d['item_id']} ({d['score_baseline']}->{d['score_candidate']})")

    change = build_change_request(diff)
    qms_dir = store.root / "qms"
    qms_dir.mkdir(parents=True, exist_ok=True)
    (qms_dir / "model_swap_change_request.json").write_text(json.dumps(change, indent=2, sort_keys=True))
    print(f"\n  QMS change request written: {qms_dir / 'model_swap_change_request.json'}")

    # --- Monitoring PROJECTION (clearly labeled; not real telemetry) ----------
    weak_grades = store.read_grades(weak.run_id)
    critical = [i.id for i in pack.rubric.items if i.critical]
    n = len(weak_grades)
    projected_overrides = sum(
        1 for g in weak_grades if any(g.item_scores.get(c, 0.0) <= 0 for c in critical)
    )
    print("\n=== MONITORING PROJECTION (modeled, NOT clinician telemetry) ===")
    print(f"  If gemini-2.5-flash were deployed, projected clinician-override rate")
    print(f"  (modeled as: a critical item the model got wrong on a case) = "
          f"{projected_overrides}/{n} = {projected_overrides/n:.2f}")
    print("  This is the SHAPE of signal M5 monitoring consumes; real override rates")
    print("  require production deployment and clinician-override capture.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
