# Two GPUs, one model: what did we learn?

## The short version

We tested whether an Intel Arc Pro B70 and an NVIDIA RTX 3090 could share the work of running one 7-billion-parameter language model. They could. In this particular test, however, using both cards was slower than using the RTX 3090 by itself. Splitting work by model layers was consistently faster than splitting the calculation across both cards.

That is a result about one specific setup, software build, model, and set of tasks. It is not a general ranking of Intel and NVIDIA cards.

## What we tested

- **Model:** DeepSeek-R1-Distill-Qwen-7B, Q4_K_M quantization. “7B” means roughly seven billion model parameters; Q4_K_M is a compressed representation intended to reduce memory use.
- **Software:** a pinned version of llama.cpp running through Vulkan on Windows.
- **Setups:** RTX 3090 alone, B70 alone, and both cards together using either layer splitting or tensor splitting.
- **Measurements:** 20 short benchmark processes and 280 timed measurements, with five repetitions for each measured test. The report keeps every sample and shows ranges of process medians, not just the fastest run.

## The headline numbers

For generating 64 tokens in the main depth-zero test (the smaller batch setting), the process-median ranges were:

| Setup | Generation speed |
|---|---:|
| RTX 3090 alone | 136.5–137.6 tokens/second |
| B70 alone | 97.1–97.2 tokens/second |
| Both, layers split between cards | 104.0–105.9 tokens/second |
| Both, tensor split between cards | 27.9–39.1 tokens/second |

A separate test processed a 512-token prompt with a wider batch. It produced much higher prompt-throughput numbers for every setup, but the ordering stayed the same: RTX alone first, B70 alone second, layer split third, tensor split fourth. Batch settings change the comparison substantially, so those two workloads should not be blended into one score.

“Tokens per second” is simply the amount of model text processed or produced each second. Prompt processing and text generation are different workloads, so compare them only within the same row and settings.

## Did using two cards give us more memory?

The cards have 32 GiB and 24 GiB of nominal memory, but those amounts do not become one shared 56 GiB pool. Both cards can hold parts of the model, and the model used here fit on either card by itself. We did not test a model that was too large for one card, so a capacity advantage remains an open question.

## Did the outputs match?

In one fixed-prompt check, all four setups chose the same next token at each of 32 positions. Repeated RTX and tensor captures also reproduced their saved logits exactly. But the first single-token step showed a small numerical difference in the mixed-card modes. Matching chosen tokens in this one prompt does not prove that all output probabilities are equivalent or that every model and prompt will behave the same.

## What this means—and what it does not

For this model and frozen software build, the RTX 3090 alone was the fastest choice. Layer splitting was better than tensor splitting in the measured configurations. The test does not show that adding a second card is never useful: it may help with other models or workloads, especially when a model cannot fit on one card.

This was one computer, one model, short runs, and a particular build whose optional CPU instruction-set optimizations were disabled. We did not isolate the cause of tensor splitting’s slowdown, test energy efficiency, or prove a general hardware ranking.

## Explore the evidence

- [Interactive benchmark explorer](docs/index.html) — choose a workload and see the stored samples.
- [Full technical report](README.md) — detailed results and limitations; unchanged from the release candidate.
- [Method and reproduction details](METHOD.md).
- [Every timing sample](data/samples.csv).
- [Offline calculation checks](VERIFY.md).

This compact preview omits the large full-logit numerical archive and pinned llama.cpp source archive. They remain separate release assets for a later, approved distribution.
