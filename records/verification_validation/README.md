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
casebank (runs `aa75fb2beedbe46e` = gemini-2.5-flash `gemini_contract`,
`9d1cfd7827de6129` = gemini-3.5-flash `gemini_contract_35`, seed 1, pack_hash
`8aacabc15a74db73…`), superseding the records generated from the earlier
NC-ND-derived case text.

The judge is now declared in the pack (`pack/judge.yaml`), so each record pins
`judge_id: geval-gemini-flash-lite` — the reference-aware `gemini-flash-lite-latest`
G-Eval judge that actually graded these runs. Records promoted before that change
pinned `judge_id: fake-judge` while a real judge graded them, because the run
scripts constructed the judge outside the pack; those records are superseded by
these. Note that `gemini-flash-lite-latest` is a floating provider alias — the pin
records the alias, not a resolved model build.
