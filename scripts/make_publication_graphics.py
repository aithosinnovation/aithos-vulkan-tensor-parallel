"""Render publication cards from the preserved nanosecond timings in data/summary.json.

The bars start at zero and end at the upper process median. A lighter tip spans
the two process medians; the printed numbers are the exact rounded range.
"""
from __future__ import annotations

import json
import statistics
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
SUMMARY = json.loads((ROOT / "data/summary.json").read_text())

BG = "#0B141B"
PANEL = "#14232D"
TRACK = "#22343D"
WHITE = "#F5F7F5"
MUTED = "#B8C8CD"
TEAL = "#52DDC0"
COLORS = {"rtx": "#52DDC0", "layer": "#78ACDF", "b70": "#A8B6C4", "tensor": "#CE94AB"}
LABELS = {"rtx": "RTX 3090 alone", "layer": "Equal 1/1 layer split",
          "b70": "Arc Pro B70 alone", "tensor": "Equal 1/1 tensor split"}
ORDER = tuple(LABELS)

plt.rcParams.update({"font.family": "DejaVu Sans", "svg.fonttype": "none",
                     "svg.hashsalt": "aithos-primary-generation-c93decc",
                     "figure.facecolor": BG, "savefig.facecolor": BG})


def process_medians(test: str, blocks: str, prompt: int, generated: int, batch: int) -> dict:
    out = {}
    for mode in ORDER:
        medians = []
        for block in blocks:
            stored = [entry for entry in SUMMARY["records"] if entry["block"] == block
                      and entry["mode"] == mode and entry["test"] == test]
            assert len(stored) == 1, (block, mode, test)
            row = stored[0]
            assert (row["n_prompt"], row["n_gen"], row["depth"], row["batch"], row["ubatch"]) == (prompt, generated, 0, batch, batch)
            rates = [(prompt + generated) * 1e9 / ns for ns in row["samples_ns"]]
            median = statistics.median(rates)
            assert abs(row["median"] - median) < 1e-9
            medians.append(median)
        assert len(medians) == 2
        out[mode] = (min(medians), max(medians))
    return out


def save(fig, name: str) -> None:
    fig.savefig(ASSETS / f"{name}.png", dpi=160,
                metadata={"Software": "Aithos Tech Lab / matplotlib 3.10.7"})
    fig.savefig(ASSETS / f"{name}.svg",
                metadata={"Date": "2026-10-31T00:00:00Z", "Creator": "Aithos Tech Lab"})
    path = ASSETS / f"{name}.svg"
    path.write_text("\n".join(line.rstrip() for line in path.read_text().splitlines()) + "\n")
    plt.close(fig)


def base(width: int, height: int):
    fig = plt.figure(figsize=(width / 160, height / 160), dpi=160)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, width)
    ax.set_ylim(height, 0)
    ax.axis("off")
    return fig, ax


def text(ax, x, y, value, size, *, color=WHITE, weight="normal", va="top", **kw):
    return ax.text(x, y, value, fontsize=size, color=color, fontweight=weight,
                   ha="left", va=va, **kw)


def rows(ax, data: dict, *, first_y: int, step: int, x: int,
         bar_width: int, max_rate: int, number_x: int,
         label_size: int, number_size: int, bar_height: int,
         number_header_y: int):
    text(ax, x, number_header_y, "Throughput · tokens/sec", 13, color=MUTED)
    text(ax, number_x, number_header_y, "Process-median range", 13, color=MUTED)
    for index, mode in enumerate(ORDER):
        low, high = data[mode]
        y = first_y + index * step
        text(ax, x, y, LABELS[mode], label_size, weight="bold")
        text(ax, number_x, y, f"{low:.1f}–{high:.1f}", number_size, weight="bold")
        by = y + 68 if step >= 180 else y + 55
        ax.add_patch(FancyBboxPatch((x, by), bar_width, bar_height,
                                   boxstyle=f"round,pad=0,rounding_size={bar_height / 2}",
                                   linewidth=0, facecolor=TRACK))
        lo_width = bar_width * low / max_rate
        hi_width = bar_width * high / max_rate
        ax.add_patch(FancyBboxPatch((x, by), hi_width, bar_height,
                                   boxstyle=f"round,pad=0,rounding_size={bar_height / 2}",
                                   linewidth=0, facecolor=COLORS[mode]))
        # The translucent tip represents the interval between the two process medians.
        if hi_width - lo_width >= 4:
            ax.add_patch(Rectangle((x + lo_width, by), hi_width - lo_width,
                                   bar_height, facecolor=WHITE, alpha=.42, linewidth=0))
        ax.plot([x + lo_width, x + lo_width], [by - 7, by + bar_height + 7],
                color=WHITE, lw=1.3, alpha=.9)


def generation_square(data: dict):
    fig, ax = base(1600, 1600)
    text(ax, 115, 86, "AITHOS  /  TECH LAB", 16, color=TEAL, weight="bold")
    ax.plot([115, 1485], [148, 148], color="#2A4A52", lw=2)
    text(ax, 115, 202, "More GPUs didn't", 38, weight="bold")
    text(ax, 115, 304, "win this test.", 38, weight="bold")
    text(ax, 115, 430, "RTX 3090 alone led our 7B", 23)
    text(ax, 115, 497, "Vulkan inference benchmark.", 23)
    ax.add_patch(FancyBboxPatch((115, 604), 1370, 730,
                                boxstyle="round,pad=0,rounding_size=24",
                                linewidth=1.2, edgecolor="#2E4850", facecolor=PANEL))
    rows(ax, data, first_y=695, step=151, x=160, bar_width=970,
         max_rate=145, number_x=1170, label_size=18, number_size=18,
         bar_height=26, number_header_y=635)
    text(ax, 115, 1380, "64-token generation · depth 0 · requested batch 32", 16, color=WHITE)
    text(ax, 115, 1430, "One Windows host · one 7B model · equal 1/1 splits", 15, color=MUTED)
    text(ax, 115, 1476, "Ranges from two benchmark processes per mode. CPU optional ISA off.",
         12, color=MUTED)
    save(fig, "generation-primary-square")


def generation_wide(data: dict):
    fig, ax = base(1920, 1080)
    text(ax, 100, 69, "AITHOS  /  TECH LAB", 16, color=TEAL, weight="bold")
    ax.plot([100, 1820], [125, 125], color="#2A4A52", lw=2)
    text(ax, 100, 173, "More GPUs didn't win this test.", 34, weight="bold")
    text(ax, 100, 265, "RTX 3090 alone led our 7B Vulkan inference benchmark.", 20)
    text(ax, 100, 344, "PRIMARY RESULT   ·   64-token generation   ·   depth 0   ·   requested batch 32", 14,
         color=MUTED, weight="bold")
    ax.add_patch(FancyBboxPatch((100, 393), 1720, 490,
                                boxstyle="round,pad=0,rounding_size=20",
                                linewidth=1.2, edgecolor="#2E4850", facecolor=PANEL))
    rows(ax, data, first_y=462, step=106, x=150, bar_width=1190,
         max_rate=145, number_x=1400, label_size=17, number_size=18,
         bar_height=22, number_header_y=412)
    text(ax, 100, 935, "One Windows host · one 7B model · equal 1/1 splits · two process medians per mode", 15)
    text(ax, 100, 987, "Pinned llama.cpp Vulkan c93decc · optional CPU ISA off · this is not a general GPU ranking", 12,
         color=MUTED)
    save(fig, "generation-primary-wide")


def prompt_support(data: dict):
    fig, ax = base(1920, 1080)
    text(ax, 100, 69, "AITHOS  /  TECH LAB", 16, color=TEAL, weight="bold")
    ax.plot([100, 1820], [125, 125], color="#2A4A52", lw=2)
    text(ax, 100, 173, "Prompt throughput at a wider batch", 34, weight="bold")
    text(ax, 100, 265, "Separate post-hoc check; RTX 3090 alone still led.", 20)
    text(ax, 100, 344, "512-token prompt   ·   depth 0   ·   requested batch and micro-batch 512", 14,
         color=MUTED, weight="bold")
    ax.add_patch(FancyBboxPatch((100, 393), 1720, 490,
                                boxstyle="round,pad=0,rounding_size=20",
                                linewidth=1.2, edgecolor="#2E4850", facecolor=PANEL))
    rows(ax, data, first_y=462, step=106, x=150, bar_width=1190,
         max_rate=5500, number_x=1400, label_size=17, number_size=18,
         bar_height=22, number_header_y=412)
    text(ax, 100, 935, "One Windows host · one 7B model · equal 1/1 splits · two process medians per mode", 15)
    text(ax, 100, 987, "Both batch settings changed together. Compare separately from primary generation; CPU optional ISA off.",
         12, color=MUTED)
    save(fig, "prompt-posthoc-wide")


def main():
    generation = process_medians("tg64-d0", "AB", 0, 64, 32)
    prompt = process_medians("pp512-d0-b512", "DE", 512, 0, 512)
    assert {m: f"{v[0]:.1f}–{v[1]:.1f}" for m, v in generation.items()} == {
        "rtx": "136.5–137.6", "layer": "104.0–105.9",
        "b70": "97.1–97.2", "tensor": "27.9–39.1"}
    generation_square(generation)
    generation_wide(generation)
    prompt_support(prompt)
    print("Wrote square and wide primary cards plus separate post-hoc prompt card from published nanosecond timings.")


if __name__ == "__main__":
    main()
