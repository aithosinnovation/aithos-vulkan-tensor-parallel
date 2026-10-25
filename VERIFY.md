# Verify the published timing data

Run with standard-library Python 3.12:

```
python3 scripts/verify.py
```

This checks all 280 published samples against their reported rates, process medians and ranges; matched-block ratios; effective context and batch settings; explorer JSON/JavaScript; and the SHA-256 manifest. It runs no benchmark, download, host snapshot, or access to private captures.

Original benchmark logs and full logit captures remain private. Their producer-level and numerical validations were completed before publication packaging. `data/correctness.json` contains summarized token and numerical-error findings; full logits and execution captures are not distributed. The numerical archive validator is retained in `scripts/verify_numerical.py` for private reproduction, but its input archive is not distributed.

The tested llama.cpp source is pinned by exact upstream commit in `README.md`; this repository does not bundle a second copy of upstream source. No model weights or inference binaries are included.
