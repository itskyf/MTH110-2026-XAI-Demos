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
from matplotlib.font_manager import FontProperties
from matplotlib.patches import Rectangle
from transformers import AutoTokenizer

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
        0.99,
        "MÔ HÌNH GỐC  ·  Ưu thế A/B ở token trả lời đầu tiên",
        weight="bold",
        va="top",
        fontsize=15,
    )
    question = case["question"].splitlines()[0]
    contrast_label = (
        case["correct_label"]
        if case["contrast_score"] > 0
        else case["alternative_label"]
    )
    for y, name, cue, choice, score in (
        (
            0.62,
            "clean",
            case["correct_label"],
            case["selected_label"],
            case["clean_score"],
        ),
        (
            0.27,
            "contrast",
            case["alternative_label"],
            contrast_label,
            case["contrast_score"],
        ),
    ):
        _diagram_box(model_axis, 0.13, y, f"x_{name}: {question}\nCue: {cue}")
        _diagram_box(model_axis, 0.34, y, "Qwen")
        _diagram_box(model_axis, 0.55, y, f"logits A/B\nchọn {choice}")
        _diagram_box(model_axis, 0.78, y, f"F({name}) = {score:.3f}", "#e8f2ec")
        for left, right in ((0.23, 0.29), (0.39, 0.46), (0.63, 0.70)):
            _diagram_arrow(model_axis, (left, y), (right, y))
    _diagram_arrow(model_axis, (0.91, 0.58), (0.91, 0.31))
    model_axis.text(
        0.92,
        0.45,
        f"ΔF_input\n{case['input_delta']:.3f}",
        va="center",
        fontsize=13,
        weight="bold",
    )


def _draw_signed_prompt(
    axis: Axes,
    case: dict,
    tokenizer: AutoTokenizer,
    *,
    size: int,
    scale: float,
) -> None:
    """Show each frozen user-token attribution behind readable prompt text."""
    tokens = tokenizer.convert_ids_to_tokens(case["clean_token_ids"])
    end = tokens.index("<|im_end|>")
    check(
        all(value == 0 for value in case["token_attribution"][:3])
        and all(value == 0 for value in case["token_attribution"][end:]),
        f"{case['case']}: omitted chat-structure attribution differs",
    )
    lines: list[list[tuple[str, float, int]]] = [[]]
    for position in range(3, end):
        value = case["token_attribution"][position]
        parts = tokenizer.decode([case["clean_token_ids"][position]]).split("\n")
        for index, part in enumerate(parts):
            if part:
                lines[-1].append((part, value, position))
            if index < len(parts) - 1:
                lines[-1].append(("↵", value, position))
                lines.append([])
    max_rows = 6
    check(len(lines) <= max_rows, f"{case['case']}: prompt heatmap exceeds panel")
    axis.set(xlim=(0, 1), ylim=(0, 8))
    axis.axis("off")
    axis.figure.canvas.draw()
    font = FontProperties(family="DejaVu Sans Mono", size=size)
    char_px = axis.figure.canvas.get_renderer().get_text_width_height_descent(
        "M", font, ismath=False
    )[0]
    char_fraction = char_px / axis.bbox.width
    check(
        all(
            sum(len(piece) for piece, _, _ in line) * char_fraction <= 1
            for line in lines
        ),
        f"{case['case']}: prompt heatmap exceeds panel width",
    )
    colors = plt.get_cmap("RdBu")
    for row, line in enumerate(lines):
        y = 0.83 - 0.12 * row
        cursor = 0
        for piece, value, position in line:
            color = colors((value / scale + 1) / 2)
            face = tuple(0.53 + 0.47 * channel for channel in color[:3])
            axis.add_patch(
                Rectangle(
                    (cursor * char_fraction, y - 0.047),
                    len(piece) * char_fraction,
                    0.094,
                    transform=axis.transAxes,
                    facecolor=face,
                    edgecolor="#217a42" if position == case["cue_position"] else "none",
                    linewidth=1.7 if position == case["cue_position"] else 0,
                )
            )
            cursor += len(piece)
        axis.text(
            0,
            y,
            "".join(piece for piece, _, _ in line),
            transform=axis.transAxes,
            fontproperties=font,
            va="center",
        )


def render_arithmetic_comparison(data: dict, tokenizer: AutoTokenizer) -> None:
    """Map the frozen arithmetic behavior to distinct evidence and limits."""
    case = next(case for case in data["cases"] if case["case"] == "arithmetic")
    plt.rcParams["font.family"] = "Liberation Sans"
    fig = plt.figure(figsize=(16, 9.5), layout="constrained")
    grid = fig.add_gridspec(
        5, 2, height_ratios=(0.9, 2.2, 2.4, 3.2, 0.75), hspace=0.2, wspace=0.15
    )
    title_axis = fig.add_subplot(grid[0, :])
    title_axis.axis("off")
    title_axis.text(
        0.01,
        0.95,
        "SỐ HỌC: LỰA CHỌN ĐO ĐƯỢC ≠ LỜI TỰ GIẢI THÍCH",
        fontsize=20,
        weight="bold",
        color="#a43432",
        va="top",
    )
    title_axis.text(
        0.01,
        0.05,
        "Cue tác động lên F ở ba phép đo khác nhau; không xác lập cơ chế đầy đủ.",
        fontsize=13,
        va="bottom",
    )
    _draw_model_runs(fig.add_subplot(grid[1, :]), case)

    explanation = " ".join(case["self_explanation"].replace("**", "").split())
    check(
        f"{case['correct_label']})" in explanation,
        "arithmetic: explanation label differs",
    )
    self_axis = fig.add_subplot(grid[2, :])
    self_axis.axis("off")
    self_axis.text(
        0.02,
        0.95,
        "TỰ GIẢI THÍCH  ·  Lượt hỏi riêng sau khi đo lựa chọn",
        weight="bold",
        va="top",
        fontsize=15,
    )
    _diagram_box(
        self_axis,
        0.17,
        0.52,
        f"Prompt riêng: câu hỏi + Cue: {case['correct_label']}\n"
        f"+ nhãn đã chọn {case['selected_label']}",
    )
    _diagram_box(self_axis, 0.40, 0.52, "Qwen")
    _diagram_arrow(self_axis, (0.32, 0.52), (0.35, 0.52))
    _diagram_arrow(self_axis, (0.45, 0.52), (0.50, 0.52))
    self_axis.text(
        0.51, 0.63, textwrap.fill(explanation, width=72), va="center", fontsize=13
    )
    self_axis.text(
        0.51,
        0.08,
        f"BẤT ĐỒNG: phát biểu {case['correct_label']} ≠ "
        f"lựa chọn đo được {case['selected_label']}.\n"
        "Không thể coi đây là giải thích trung thực cho lựa chọn đã đo.",
        color="#b33d39",
        weight="bold",
        fontsize=13,
    )

    ig_axis = fig.add_subplot(grid[3, 0])
    patch_axis = fig.add_subplot(grid[3, 1])
    note_axes = [fig.add_subplot(grid[4, column]) for column in range(2)]
    patch_axis.plot(range(len(case["patch_deltas"])), case["patch_deltas"], marker=".")
    patch_axis.axhline(0, color="black", linewidth=0.5)
    patch_axis.set(xlabel="Tầng decoder", ylabel="ΔF_patch")
    patch_axis.set_title(
        "PATCH  ·  Kích hoạt cue clean/contrast + F → ΔF theo tầng",
        loc="left",
        fontsize=14,
        weight="bold",
    )
    for note_axis, message in zip(
        note_axes,
        (
            (
                "Cue có attribution dương trên đường baseline → clean;\n"
                "không chứng minh cơ chế nhân quả."
            ),
            (
                "Phục hồi biểu diễn cue làm F đổi ở tầng đầu;\n"
                "không chứng minh tính cần thiết hay cơ chế đầy đủ."
            ),
        ),
        strict=True,
    ):
        note_axis.axis("off")
        note_axis.text(0, 0.8, message, va="top", fontsize=12, color="#34495e")
    scale = max(
        abs(value) for item in data["cases"] for value in item["token_attribution"]
    )
    _draw_signed_prompt(ig_axis, case, tokenizer, size=14, scale=scale)
    ig_axis.text(
        0,
        7.7,
        "IG · embedding clean + baseline + F → token IG",
        weight="bold",
        fontsize=13,
    )
    cue_value = case["token_attribution"][case["cue_position"]]
    ig_axis.text(
        0,
        0.25,
        f"Viền xanh: cue {case['correct_label']} = {cue_value:+.3f} · "
        "đỏ giảm F → y-; xanh tăng F → y+",
        fontsize=12,
    )

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
        len(data["cases"]), 1, figsize=(10, 8.2), layout="constrained"
    )
    scale = max(
        abs(value) for case in data["cases"] for value in case["token_attribution"]
    )
    for axis, case in zip(axes, data["cases"], strict=True):
        _draw_signed_prompt(axis, case, tokenizer, size=14, scale=scale)
        cue_value = case["token_attribution"][case["cue_position"]]
        axis.text(
            0,
            7.65,
            f"{case['case'].capitalize()} · "
            f"cue {case['correct_label']} = {cue_value:+.3f}",
            fontsize=15,
            weight="bold",
        )
        axis.text(
            0,
            0.25,
            "Viền xanh: cue đóng băng · ↵: xuống dòng · token cấu trúc chat có IG = 0",
            fontsize=11,
        )
    fig.suptitle(
        "IG có dấu theo token · cùng thang màu ±"
        f"{scale:.3f}: đỏ giảm F về y-; xanh tăng F về y+",
        fontsize=14,
    )
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
