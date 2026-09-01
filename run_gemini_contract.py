#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Extract the input contract from a REAL model (gemini-2.5-flash) on TCGA-LUAD.

Runs the `gemini_contract` battery (ablation + format) so the information-value
curve reflects a real model's real behaviour: withhold the pathology report and
the model can no longer state the diagnosis, etc. Grading is done by the judge
the pack declares in `pack/judge.yaml` (pinned, reference-aware) — this script
only orchestrates, so the judge each run pins is the judge that graded it.
Requires GEMINI_API_KEY.
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from validrig.execute import run_battery
from validrig.packio.loader import load_pack
from validrig.store.runstore import RunStore

ROOT = Path(__file__).parent


def main() -> int:
    if not os.environ.get("GEMINI_API_KEY"):
        print("Set GEMINI_API_KEY first.")
        return 1
    pack = load_pack(ROOT / "pack")
    store = RunStore(ROOT / "runs")
    battery = sys.argv[1] if len(sys.argv) > 1 else "gemini_contract"
    judge_spec = pack.judge_for(battery)
    now = lambda: datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    print(f"Running {battery} (ablation, judge={judge_spec.id} / "
          f"{judge_spec.binding.get('model_id')}, declared in pack/judge.yaml) ...")
    r = run_battery(pack, battery, store, seed=1, now=now)[0]
    print(f"\nrun={r.run_id} sut={r.sut_id} units={r.n_units} acceptance="
          f"{'PASS' if r.report['acceptance']['overall_pass'] else 'FAIL'}")
    print(f"\n=== INPUT CONTRACT on {r.sut_id} (real model, real data) ===")
    for e in r.contract["elements"]:
        iv = e["information_value"]
        print(f"  {e['name']:20} measured={e['measured']!s:5} "
              f"information_value={'—' if iv is None else round(iv, 3)}")
    print("  minimal sufficient set:", r.contract["minimal_sufficient_set_candidate"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
