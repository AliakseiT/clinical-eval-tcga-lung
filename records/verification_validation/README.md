# Verification & validation records

Retained, controlled V&V records for this project — stored **exactly as they
would be in a real deployment** (this repo is the example; the records inside it
are not "examples"). Transient run outputs live in `runs/` (gitignored); a record
is *promoted* here after review, and would be signed and anchored to an immutable
release before use as QMS evidence.

| Record | What |
|---|---|
| [`vvr-gemini-2.5-flash.md`](vvr-gemini-2.5-flash.md) | Validation dossier — gemini-2.5-flash on TCGA-LUAD (`.html` = printable) |
| [`vvr-gemini-3.5-flash.md`](vvr-gemini-3.5-flash.md) | Validation dossier — gemini-3.5-flash |
| [`deid-recall-evaluation.md`](deid-recall-evaluation.md) | De-identification recall of the ingestion config (before/after clinical recognizers) |

Open the `.md` to read on GitHub; open the `.html` in a browser to print
(Cmd/Ctrl-P). The `.json` is the structured record each is rendered from.

All are **DRAFT / unsigned**; signer roles are clinical (medical + quality
reviewer). Regenerate: `rig dossier …` (V&V) / `python run_deid_eval.py` (de-id).

All records were regenerated 2026-08-30 from runs on the committed GDC-sourced
casebank (runs `fbb6b102ea4b33cd` = gemini-2.5-flash `gemini_contract`,
`a4ec2e5573b1b0cd` = gemini-3.5-flash `gemini_contract_35`, seed 1, judge
`gemini-flash-lite-latest`, reference-aware), superseding the records generated
from the earlier NC-ND-derived case text.
