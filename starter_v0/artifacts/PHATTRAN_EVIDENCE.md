# Local optimization evidence — Phat Tran

## Milestones and provenance

- Group v0: `runs/v0_B_base_openai_20261110T103134879229.json`, 14/20, OpenAI gpt-4o-mini. Accepted shared baseline. Its recorded artifact hashes differ from committed starter files; cause remains unresolved.
- v1 milestone: `runs/v1_B_base_openrouter_20261110T105550757260.json`, 19/20, OpenRouter openai/gpt-4o-mini. R12 calls clarify with text instead of expected yes_no. Historical prompt hash 8651a9c7c23b… is recorded in the run; exact prompt bytes have NOT been recovered. Supplied 95% text is retained as an explicitly unverified reconstruction.
- v2 milestone: `runs/v1_B_base_openrouter_20261110T110234512358.json`, 20/20, same OpenRouter/model and tools hash as selected v1. Exact prompt/tools snapshots are verified against the source run. The active artifacts equal v2.
- Both selected raw runs were originally labeled v1 during local experimentation. Milestone naming is retrospective, documented in milestone_mapping.json; no raw JSON was relabeled or edited. Other local trials are retained, including provider timeout trials and early v2-labeled runs with unchanged starter hashes.
- The supplied prompt texts suggest removing conflicting single-step/confirmation rules and adding confirmation precedence. Exact historical v1-to-v2 diff is not verified. The 95% artifact cannot yet be claimed reproducible.

## Limits of measured results

100% means routing/argument correctness on 20 base cases, not end-to-end service success. The final run contains Twitter API45 HTTP 403/429 errors; earlier trials include timeout and fetch of a 404 page. No-tool grading does not establish that R08/R14 correctly refuse out-of-scope requests. OpenAI shared v0 versus OpenRouter local results are not a controlled provider comparison; do not attribute all 70%→100% improvement to prompt changes. No new live API runs were performed while organizing these files.

## Chat evidence

`transcripts/v1_openrouter_20261110T110611705480.transcript.json` matches v2 prompt/tools hashes, although its original label is v1. Four turns: asks account without guessing; asks whether to prepare Telegram content; asks destination using clarify(text); accepts cancellation. No send call occurs. Turns 1/2 ask in plain text without invoking clarify, despite the prompt requirement. Final sending after exact-content/destination confirmation was not tested. The transcript supports cancellation/no-premature-send behavior in this conversation only.

## Validation and remaining work

Full offline pytest: 62 passed, 17 skipped, 1 LibreSSL warning. TODO tests remain skipped; this is not completion of the 0-skipped checklist. Contract tests pass within the full suite. eval_base.json is unchanged by this contribution.

Still required for the final group submission: recover/verify historical v1 prompt (or conduct an explicitly new, separately labeled reproducibility run); a genuine v3 hypothesis/change with evidence; team eval cases; new tool and tests; complete group report and UI validation. The existing branch already contains teammates' baseline and Streamlit UI; this contribution does not claim to have authored or validated them.

Original run/transcript files are preserved. No .env, credentials or virtual environment is included.
