"""Check the frozen numerical evidence and plot its case-level results."""

import json
import math
from pathlib import Path

import matplotlib as mpl

mpl.use("Agg")
import matplotlib.pyplot as plt
from transformers import AutoTokenizer

SOURCE = Path("data/frozen.json")
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


def render(data: dict) -> None:
    """Plot signed token attribution and layer-wise patch effects."""
    tokenizer = AutoTokenizer.from_pretrained(
        data["tokenizer"], revision=data["tokenizer_revision"]
    )
    FIGURES.mkdir(exist_ok=True)
    plt.rcParams["svg.fonttype"] = "none"

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
            fontsize=7,
        )
        axis.legend(loc="upper right")
    fig.savefig(FIGURES / "integrated-gradients-token-attribution.svg")
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
    fig.savefig(FIGURES / "activation-patching-layer-effects.svg")
    plt.close(fig)


if __name__ == "__main__":
    render(load())
