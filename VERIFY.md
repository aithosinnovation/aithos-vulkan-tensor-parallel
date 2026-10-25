# Verify the published timing data

Run with standard-library Python 3.12:

```
python3 scripts/verify.py
```

This recomputes all 280 sample rates from `(n_prompt + n_gen) * 1e9 / elapsed_ns`, compares CSV samples with the summary, and checks all 56 process medians and ranges. It checks matched-block medians, ratios, percentage changes, range-overlap flags, ratio ranges, and direction flags. It compares the CSV's requested/effective settings with the summary, confirms the explorer JSON/JavaScript payloads equal the summary, and checks the SHA-256 of each file listed in the manifest. These checks run with standard-library Python and need no GPU.

The effective-setting check establishes CSV/summary agreement; it does not independently derive context or batch behavior from llama.cpp source or native logs. The script does not check prose, README/HTML tables, figures, correctness metrics, memory/telemetry claims, or private device-allocation evidence. File hashes establish integrity against the manifest, not factual correctness. It runs no benchmark, download, host snapshot, or access to private captures.

Text files use LF line endings, enforced by `.gitattributes`, so the manifest describes the same bytes on Windows and Unix checkouts. Avoid converting the release files to CRLF before verification. Run the command from a clean checkout or extracted release.

Original benchmark logs and full logit captures remain private. Their producer-level and numerical validations were completed before publication packaging. `data/correctness.json` contains summarized token and numerical-error findings; full logits and execution captures are not distributed. The numerical archive validator is retained in `scripts/verify_numerical.py` for private reproduction, but its input archive is not distributed.

The tested llama.cpp source is pinned by exact upstream commit in `README.md`; this repository does not bundle a second copy of upstream source. No model weights or inference binaries are included.
