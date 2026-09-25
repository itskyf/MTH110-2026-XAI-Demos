"""Verify the released run and render its case-level coursework evidence."""

import hashlib
import json
import math
import re
from pathlib import Path

import matplotlib as mpl

mpl.use("Agg")
import matplotlib.pyplot as plt
from transformers import AutoTokenizer

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/frozen.json"
REPORT = ROOT / "docs/report"
DIGEST = "23a674f0276156e182c554b81cd3f56fda84b565d726d3efc3319cdd67520728"
REVISION = "c1899de289a04d12100db370d81485cdf75e47ca"
NAMES = ("calibration", "arithmetic", "logic")
IG_STEPS = 1024
LAYERS = 28


def check(condition: object, message: str) -> None:
    """Reject inconsistent released evidence before producing outputs."""
    if not condition:
        raise ValueError(message)


def load() -> dict:
    """Read only the published artifact identity and verify its frozen fields."""
    raw = SOURCE.read_bytes()
    check(hashlib.sha256(raw).hexdigest() == DIGEST, "Release artifact SHA-256 differs")
    data = json.loads(raw)
    check(data["model"] == "Qwen/Qwen3-0.6B", "Model differs from protocol")
    check(data["revision"] == REVISION, "Model revision differs from protocol")
    check(data["tokenizer_revision"] == REVISION, "Tokenizer revision differs")
    check(
        data["target_score"] == "correct_minus_alternative_next_token_logits",
        "Target score differs",
    )
    check(
        data["ig_method"] == "riemann_middle" and data["ig_steps"] == IG_STEPS,
        "IG procedure differs",
    )
    check(data["ig_aggregation"] == "signed_embedding_sum", "IG aggregation differs")
    check(
        data["input_intervention"] == "contrast_score_minus_clean_score",
        "Input effect differs",
    )
    check(data["patch_direction"] == "clean_to_contrast", "Patch direction differs")
    check(
        data["patch_location"] == "cue_token_full_layer_output",
        "Patch location differs",
    )
    check(tuple(case["case"] for case in data["cases"]) == NAMES, "Frozen cases differ")

    for case in data["cases"]:
        name = case["case"]
        clean, contrast = case["clean_token_ids"], case["contrast_token_ids"]
        cue = case["cue_position"]
        changed = [
            i for i, (a, b) in enumerate(zip(clean, contrast, strict=True)) if a != b
        ]
        check(changed == [cue], f"{name}: cue-token alignment differs")
        check(
            len(clean) == len(case["token_attribution"]),
            f"{name}: attribution length differs",
        )
        check(
            len(case["patched_scores"]) == len(case["patch_deltas"]) == LAYERS,
            f"{name}: patch sweep differs",
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
    """Write report-ready evidence without changing the released results."""
    tokenizer = AutoTokenizer.from_pretrained(data["tokenizer"], revision=REVISION)
    figures = REPORT / "figures"
    figures.mkdir(exist_ok=True)
    plt.rcParams["svg.hashsalt"] = "mth110-frozen"
    plt.rcParams["svg.fonttype"] = "none"

    fig, axes = plt.subplots(3, 1, figsize=(16, 12), layout="constrained")
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
    fig.savefig(figures / "token-attribution.svg", metadata={"Date": None})
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
    fig.savefig(figures / "patch.svg", metadata={"Date": None})
    plt.close(fig)
    for path in figures.glob("*.svg"):
        svg = re.sub(
            r"<!DOCTYPE svg PUBLIC.*?>\n| <metadata>.*?</metadata>\n",
            "",
            path.read_text(),
            flags=re.DOTALL,
        )
        path.write_text("\n".join(line.rstrip() for line in svg.splitlines()) + "\n")

    lines = [
        "// Generated by scripts/analyze_frozen.py from v1.0.0/frozen.json.",
        "= Frozen case evidence",
        "",
        "#table(",
        "  columns: 7,",
        "  [Case],",
        "  [Selected],",
        "  [F clean],",
        "  [F contrast],",
        "  [Input effect],",
        "  [Cue IG],",
        "  [IG residual],",
        "",
    ]
    for case in data["cases"]:
        cells = (
            case["case"],
            case["selected_label"],
            f"{case['clean_score']:.3f}",
            f"{case['contrast_score']:.3f}",
            f"{case['input_delta']:.3f}",
            f"{case['token_attribution'][case['cue_position']]:.3f}",
            f"{case['ig_completeness_delta']:.6f}",
        )
        lines.append("  " + ", ".join(f"[{cell}]" for cell in cells) + ",")
    lines += [
        ")",
        "",
        "All scores are correct-label minus alternative-label next-token logits.",
        (
            "Cue IG is the signed attribution at the pre-specified cue token. "
            "The IG residual is the recorded completeness diagnostic."
        ),
        "",
        "#figure(",
        '  image("figures/token-attribution.svg", width: 100%),',
        (
            "  caption: [Signed token attributions for every frozen case; "
            "the green line marks the cue token.],"
        ),
        ")",
        "",
        "#figure(",
        '  image("figures/patch.svg", width: 100%),',
        (
            "  caption: [Layer-wise effect of replacing the contrast cue "
            "activation with its clean value.],"
        ),
        ")",
        "",
        "== Recorded self-explanations",
        "",
    ]
    for case in data["cases"]:
        lines += [
            f"=== {case['case'].capitalize()}",
            "",
            "#quote(block: true)[#text(",
            "  " + json.dumps(case["self_explanation"], ensure_ascii=False) + ",",
            ")]",
            "",
        ]
    (REPORT / "evidence.typ").write_text("\n".join(lines))


if __name__ == "__main__":
    render(load())
