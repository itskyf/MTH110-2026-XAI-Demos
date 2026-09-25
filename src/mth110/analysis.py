"""Check the frozen numerical evidence, write a summary, and plot case-level results."""

import csv
import json
import math
import textwrap
from pathlib import Path

import matplotlib as mpl

mpl.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from transformers import AutoTokenizer, PreTrainedTokenizerBase

SOURCE = Path("data/frozen.json")
SUMMARY = Path("data/evidence-summary.csv")
FIGURES = Path("docs/report/figures")


def check(condition: object, message: str) -> None:
    """Reject inconsistent released evidence before producing outputs."""
    if not condition:
        raise ValueError(message)


def load() -> dict:
    """Check the recorded numerical diagnostics."""
    data = json.loads(SOURCE.read_text())
    check(
        tuple(case["case"] for case in data["cases"])
        == ("calibration", "arithmetic", "logic"),
        "Frozen case set differs",
    )
    for case in data["cases"]:
        name = case["case"]
        check(
            len(case["token_attribution"]) == len(case["clean_token_ids"])
            and 0 <= case["cue_position"] < len(case["clean_token_ids"]),
            f"{name}: token attribution alignment differs",
        )
        values = [
            case[key]
            for key in (
                "clean_score",
                "contrast_score",
                "input_delta",
                "baseline_score",
                "ig_completeness_delta",
            )
        ]
        values += (
            case["token_attribution"] + case["patched_scores"] + case["patch_deltas"]
        )
        check(
            all(math.isfinite(value) for value in values), f"{name}: non-finite result"
        )
        clean_score, contrast_score = case["clean_score"], case["contrast_score"]
        check(
            math.isclose(
                case["input_delta"], contrast_score - clean_score, abs_tol=1e-6
            ),
            f"{name}: input effect differs",
        )
        expected_label = (
            case["correct_label"] if clean_score > 0 else case["alternative_label"]
        )
        check(
            clean_score != 0 and case["selected_label"] == expected_label,
            f"{name}: selected label differs",
        )
        residual = sum(case["token_attribution"]) - (
            clean_score - case["baseline_score"]
        )
        check(
            math.isclose(residual, case["ig_completeness_delta"], abs_tol=1e-5),
            f"{name}: IG diagnostic differs",
        )
        check(
            all(
                math.isclose(delta, score - contrast_score, abs_tol=1e-6)
                for score, delta in zip(
                    case["patched_scores"], case["patch_deltas"], strict=True
                )
            ),
            f"{name}: patch effect differs",
        )
    return data


def write_summary(data: dict) -> None:
    """Write a local CSV summary directly from the canonical recorded values."""
    SUMMARY.parent.mkdir(exist_ok=True)
    with SUMMARY.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(
            (
                "case",
                "selected_label",
                "correct_label",
                "clean_score",
                "contrast_score",
                "input_delta",
                "cue_ig",
                "ig_completeness_delta",
            )
        )
        for case in data["cases"]:
            writer.writerow(
                (
                    case["case"],
                    case["selected_label"],
                    case["correct_label"],
                    case["clean_score"],
                    case["contrast_score"],
                    case["input_delta"],
                    case["token_attribution"][case["cue_position"]],
                    case["ig_completeness_delta"],
                )
            )


def _diagram_box(
    axis: Axes, x: float, y: float, label: str, color: str = "#edf3f8"
) -> None:
    axis.text(
        x,
        y,
        label,
        ha="center",
        va="center",
        transform=axis.transAxes,
        bbox={
            "boxstyle": "round,pad=0.45",
            "facecolor": color,
            "edgecolor": "#496678",
        },
    )


def _diagram_arrow(
    axis: Axes, start: tuple[float, float], end: tuple[float, float]
) -> None:
    axis.annotate(
        "",
        xy=end,
        xytext=start,
        xycoords="axes fraction",
        arrowprops={"arrowstyle": "->", "color": "#496678", "linewidth": 1.5},
    )


def _draw_model_runs(model_axis: Axes, case: dict) -> None:
    model_axis.axis("off")
    model_axis.text(
        0.02,
        0.88,
        "1. Đầu vào/đầu ra của mô hình gốc và điểm nghiên cứu suy ra",
        weight="bold",
        va="top",
    )
    question = case["question"].splitlines()[0]
    contrast_label = (
        case["correct_label"]
        if case["contrast_score"] > 0
        else case["alternative_label"]
    )
    for y, name, cue, choice, score in (
        (
            0.70,
            "clean",
            case["correct_label"],
            case["selected_label"],
            case["clean_score"],
        ),
        (
            0.25,
            "contrast",
            case["alternative_label"],
            contrast_label,
            case["contrast_score"],
        ),
    ):
        _diagram_box(model_axis, 0.14, y, f"x_{name}: {question}\nCue: {cue}")
        _diagram_box(model_axis, 0.36, y, "Mô hình gốc")
        _diagram_box(model_axis, 0.58, y, f"logits A/B; chọn {choice}")
        _diagram_box(model_axis, 0.78, y, f"F({name}) = {score:.3f}", "#e8f2ec")
        for left, right in ((0.24, 0.29), (0.43, 0.49), (0.68, 0.71)):
            _diagram_arrow(model_axis, (left, y), (right, y))
    _diagram_arrow(model_axis, (0.94, 0.65), (0.94, 0.33))
    model_axis.text(0.95, 0.49, f"ΔF_input\n= {case['input_delta']:.3f}", va="center")


def render_arithmetic_comparison(
    data: dict, tokenizer: PreTrainedTokenizerBase
) -> None:
    """Draw the frozen arithmetic evidence and its distinct procedure inputs."""
    case = next(case for case in data["cases"] if case["case"] == "arithmetic")
    plt.rcParams["font.family"] = "Liberation Sans"
    fig, axes = plt.subplots(
        6,
        1,
        figsize=(16, 9.5),
        layout="constrained",
        gridspec_kw={"height_ratios": (2.2, 1.15, 0.52, 2.1, 0.52, 1.6)},
    )

    _draw_model_runs(axes[0], case)

    explanation = " ".join(case["self_explanation"].replace("**", "").split())
    check(
        f"{case['correct_label']})" in explanation,
        "arithmetic: explanation label differs",
    )
    self_axis = axes[1]
    self_axis.axis("off")
    self_axis.text(
        0.02,
        0.95,
        "2. Tự giải thích: một lượt hỏi riêng sau lựa chọn A/B",
        weight="bold",
        va="top",
    )
    _diagram_box(
        self_axis,
        0.19,
        0.50,
        f"Prompt riêng: câu hỏi + Cue: {case['correct_label']}\n"
        f"+ nhãn đã chọn {case['selected_label']}",
    )
    _diagram_box(self_axis, 0.42, 0.50, "Mô hình gốc")
    _diagram_arrow(self_axis, (0.33, 0.50), (0.36, 0.50))
    _diagram_arrow(self_axis, (0.48, 0.50), (0.52, 0.50))
    self_axis.text(
        0.53, 0.67, textwrap.fill(explanation, width=82), va="center", fontsize=11
    )
    self_axis.text(
        0.53,
        0.13,
        f"Bất đồng: lời giải thích nói {case['correct_label']}; "
        f"lựa chọn đã đo là {case['selected_label']}.",
        color="#b33d39",
        weight="bold",
    )

    ig_header = axes[2]
    ig_header.axis("off")
    _diagram_box(ig_header, 0.25, 0.45, "Embedding clean + tham chiếu dấu cách + F")
    _diagram_arrow(ig_header, (0.45, 0.45), (0.53, 0.45))
    _diagram_box(ig_header, 0.74, 0.45, "3. IG có dấu theo token", "#e8f2ec")

    values = case["token_attribution"]
    positions = range(len(values))
    ig_axis = axes[3]
    ig_axis.bar(
        positions,
        values,
        color=["#c0504d" if value < 0 else "#3978a8" for value in values],
    )
    ig_axis.axhline(0, color="black", linewidth=0.5)
    ig_axis.axvline(
        case["cue_position"],
        color="#277b45",
        linewidth=1.7,
        label=f"cue (IG = {values[case['cue_position']]:.3f})",
    )
    ig_axis.set_ylabel("IG có dấu")
    ig_axis.set_xticks(
        list(positions),
        tokenizer.convert_ids_to_tokens(case["clean_token_ids"]),
        rotation=90,
        fontsize=10,
    )
    ig_axis.legend(loc="upper right")

    patch_header = axes[4]
    patch_header.axis("off")
    _diagram_box(patch_header, 0.25, 0.45, "Kích hoạt cue clean/contrast + F")
    _diagram_arrow(patch_header, (0.45, 0.45), (0.53, 0.45))
    _diagram_box(patch_header, 0.74, 0.45, "4. Hiệu ứng patch theo tầng", "#e8f2ec")

    patch_axis = axes[5]
    patch_axis.plot(range(len(case["patch_deltas"])), case["patch_deltas"], marker=".")
    patch_axis.axhline(0, color="black", linewidth=0.5)
    patch_axis.set(xlabel="Tầng decoder", ylabel="ΔF_patch")
    fig.savefig(FIGURES / "arithmetic-case-comparison.svg", metadata={"Date": None})
    plt.close(fig)


def render(data: dict) -> None:
    """Plot signed token attribution and layer-wise patch effects."""
    tokenizer = AutoTokenizer.from_pretrained(
        data["tokenizer"], revision=data["tokenizer_revision"]
    )
    FIGURES.mkdir(exist_ok=True)
    plt.rcParams.update(
        {"font.size": 13, "svg.fonttype": "none", "svg.hashsalt": "mth110"}
    )

    fig, axes = plt.subplots(
        len(data["cases"]), 1, figsize=(16, 12), layout="constrained"
    )
    for axis, case in zip(axes, data["cases"], strict=True):
        values = case["token_attribution"]
        positions = range(len(values))
        axis.bar(
            positions,
            values,
            color=["#c0504d" if value < 0 else "#3978a8" for value in values],
        )
        axis.axhline(0, color="black", linewidth=0.5)
        axis.axvline(
            case["cue_position"],
            color="#277b45",
            linewidth=1.4,
            label="frozen cue position",
        )
        axis.set_title(case["case"].capitalize())
        axis.set_ylabel("Signed IG")
        axis.set_xticks(
            list(positions),
            tokenizer.convert_ids_to_tokens(case["clean_token_ids"]),
            rotation=90,
            fontsize=10,
        )
        axis.legend(loc="upper right")
    fig.savefig(
        FIGURES / "integrated-gradients-token-attribution.svg",
        metadata={"Date": None},
    )
    plt.close(fig)

    fig, axis = plt.subplots(figsize=(9, 4), layout="constrained")
    for case in data["cases"]:
        axis.plot(
            range(len(case["patch_deltas"])),
            case["patch_deltas"],
            marker=".",
            label=case["case"],
        )
    axis.axhline(0, color="black", linewidth=0.5)
    axis.set(xlabel="Decoder layer", ylabel="Clean-to-contrast patch effect on F")
    axis.legend()
    fig.savefig(
        FIGURES / "activation-patching-layer-effects.svg",
        metadata={"Date": None},
    )
    plt.close(fig)

    render_arithmetic_comparison(data, tokenizer)
    for path in FIGURES.glob("*.svg"):
        path.write_text(
            "\n".join(line.rstrip() for line in path.read_text().splitlines()) + "\n"
        )


if __name__ == "__main__":
    evidence = load()
    write_summary(evidence)
    render(evidence)
