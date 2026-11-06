# Proposed @AithosAI X Premium post — not yet posted

Attach `assets/generation-primary-square.png`. Final X publication requires separate founder authorization.

More GPUs didn't win this test. On one Windows host, RTX 3090 alone led our 7B Vulkan inference benchmark. Equal 1/1 layer and tensor splits with an Arc Pro B70 ran the model, but neither beat the RTX alone. Layer splitting did beat the B70 alone.

We tested four paths with DeepSeek-R1-Distill-Qwen-7B Q4_K_M: RTX alone, B70 alone, equal layer split, and equal tensor split. The build was pinned to llama.cpp Vulkan c93decc; CUDA and optional CPU ISA extensions were off. Twenty sequential benchmark processes retained 280 timings. The ranges below are process medians from two depth-zero blocks per mode, not best runs or independent trials.

In the primary 64-token generation test, depth zero and requested batch/ubatch 32, throughput was:
• RTX 3090 alone: 136.5–137.6 tokens/sec
• Equal layer split: 104.0–105.9
• Arc Pro B70 alone: 97.1–97.2
• Equal tensor split: 27.9–39.1

That is the attached square graphic. Each bar starts at zero; its printed range comes from the two process medians. Tensor used the generic all-reduce fallback, and its two generation medians differed substantially. We did not isolate the cause of that spread.

We also ran a separate post-hoc 512-token prompt check at requested batch/ubatch 512. Prompt rates increased substantially relative to the primary batch-32 setting, but the four-mode order stayed RTX > layer > B70 > tensor. Both batch settings changed together; those prompt results are shown separately in the full report.

The RTX link width read ×4. Among 438 NVIDIA samples with nonzero utilization, PCIe link generation read Gen3 in 406 and Gen1 or Gen2 in 32. These ~0.5-second samples do not reveal link state during individual transfers. We have no B70 link telemetry or link A/B test and cannot attribute a share of the slowdown to OCuLink.

This 7B model fits either card. We did not test a model too large for one card, unequal splits, an ISA-enabled rebuild, or dual-GPU energy efficiency. On one fixed correctness prompt, all four modes matched 32/32 top-token IDs; that does not establish numerical equivalence or general correctness. This is one host, one model, one software pin, and an as-built implementation comparison—not a universal GPU ranking.

Credit to llama.cpp and the Vulkan tensor-parallel contributors, including pwilkin. Full report, every recorded timing, figures, reproduction steps, and limits: https://github.com/aithosinnovation/aithos-vulkan-tensor-parallel
