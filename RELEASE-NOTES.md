# Release notes

This repository publishes the Aithos mixed-vendor Vulkan benchmark report, the complete derived timing table, verification data, scripts, and a static interactive explorer. Raw execution logs and full logit captures remain private. The report identifies the tested llama.cpp commit and documents limitations alongside the results.

Original Aithos code and documentation are licensed under MIT; see `LICENSE`. The Vercel configuration routes the site root to `docs/index.html`. No backend, telemetry, model weights, or inference binaries are included.

## Accuracy review corrections — 2026-10-25

- Standardized text files to LF and regenerated the manifest from those canonical bytes. The previous manifest contained both line-ending mismatches and incorrect hashes for `assets/MEDIA.md`, `LICENSE`, `LICENSE-NOTICES.md`, and `RELEASE-NOTES.md`; normalizing line endings alone was insufficient. `.gitattributes` now enforces LF, and verification passes from fresh checkouts with Git's Windows line-ending conversion enabled or disabled.
- Corrected the beginner summary's ranking to RTX, layer split, B70, tensor split. Corrected the count of slow first repetitions from 20 to 19 of 56. Published timing measurements and headline conclusions are unchanged.
- Expanded the offline verifier to recompute rates from elapsed nanoseconds and check additional comparison fields; documented its scope and exclusions precisely.
- Clarified fresh CMake defaults, the recorded case order, and the manual 3-second pause between cases. The per-case benchmark scripts do not supply that pause.
- Corrected and pinned the description of upstream AI contribution policies.
- Qualified the highest observed PCIe state and the optimized synchronization capability requirements. Identified device-allocation assertions that rely on private logs.
- Removed the unused source-digest map from derived explorer data and retained it privately. Clarified that sanitized producer-input digests refer to files not distributed in this repository; the public manifest hashes the distributed files.
