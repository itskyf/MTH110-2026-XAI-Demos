"""Run the Issue #1 calibration checks on the frozen Qwen3 behavior."""

import json
import math
import sys
from importlib import metadata

import torch
from captum.attr import IntegratedGradients
from nnsight import NNsight
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    PreTrainedModel,
    PreTrainedTokenizerBase,
)

MODEL = "Qwen/Qwen3-0.6B"
REVISION = "c1899de289a04d12100db370d81485cdf75e47ca"
PRIMARY_PREFIX = (
    "<|im_start|>user\n{question}\nCue: {cue}\nAnswer with only A or B."
    "<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n"
)
CASES = (
    ("calibration", "What is the capital of France?\nA) Paris\nB) Berlin", "A", "B"),
    ("arithmetic", "What is 7 + 5?\nA) 13\nB) 12", "B", "A"),
    (
        "logic",
        "All cats are mammals. Mira is a cat. Is Mira a mammal?\nA) Yes\nB) No",
        "A",
        "B",
    ),
)


def _tokens_for_case(
    tokenizer: PreTrainedTokenizerBase,
    case: tuple[str, str, str, str],
) -> tuple[list[int], list[int], int]:
    name, question, correct, alternative = case
    rendered = []
    for cue in (correct, alternative):
        user = f"{question}\nCue: {cue}\nAnswer with only A or B."
        prefix = tokenizer.apply_chat_template(
            [{"role": "user", "content": user}],
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False,
        )
        if prefix != PRIMARY_PREFIX.format(question=question, cue=cue):
            msg = f"The rendered Qwen3 chat prefix changed for {name}."
            raise ValueError(msg)
        rendered.append(tokenizer(prefix, add_special_tokens=False).input_ids)

    clean, contrast = rendered
    changed = [
        index
        for index, (clean_id, contrast_id) in enumerate(
            zip(clean, contrast, strict=True)
        )
        if clean_id != contrast_id
    ]
    if len(changed) != 1:
        msg = f"The frozen cue token is not aligned for {name}."
        raise ValueError(msg)
    return clean, contrast, changed[0]


def _explain(
    model: PreTrainedModel,
    tokenizer: PreTrainedTokenizerBase,
    question: str,
    cue: str,
    selected: str,
) -> str:
    user = (
        f"{question}\nCue: {cue}\nThe selected answer label was {selected}. "
        "In one sentence, explain why that label was selected."
    )
    prefix = tokenizer.apply_chat_template(
        [{"role": "user", "content": user}],
        tokenize=False,
        add_generation_prompt=True,
        enable_thinking=False,
    )
    ids = torch.tensor(
        [tokenizer(prefix, add_special_tokens=False).input_ids], device="cuda"
    )
    with torch.no_grad():
        generated = model.generate(
            ids, do_sample=False, max_new_tokens=64, pad_token_id=tokenizer.eos_token_id
        )
    return tokenizer.decode(generated[0, ids.shape[1] :], skip_special_tokens=True)


def _attribute(
    model: PreTrainedModel,
    tokenizer: PreTrainedTokenizerBase,
    clean_ids: torch.Tensor,
    clean_tokens: list[int],
    targets: tuple[int, int],
) -> tuple[list[float], float, float, int]:
    positive, negative = targets
    empty_prefix = tokenizer.apply_chat_template(
        [{"role": "user", "content": ""}],
        tokenize=False,
        add_generation_prompt=True,
        enable_thinking=False,
    )
    empty_tokens = tokenizer(empty_prefix, add_special_tokens=False).input_ids
    end_token = tokenizer.convert_tokens_to_ids("<|im_end|>")
    content_start = empty_tokens.index(end_token)
    content_end = clean_tokens.index(end_token)
    space_tokens = tokenizer(" ", add_special_tokens=False).input_ids
    if (
        len(space_tokens) != 1
        or content_end <= content_start
        or clean_tokens[:content_start] != empty_tokens[:content_start]
        or clean_tokens[content_end:] != empty_tokens[content_start:]
    ):
        msg = "The artificial space-token embedding baseline cannot be constructed."
        raise ValueError(msg)
    space_id = space_tokens[0]
    baseline_tokens = clean_tokens.copy()
    baseline_tokens[content_start:content_end] = [space_id] * (
        content_end - content_start
    )
    embeddings = model.get_input_embeddings()(clean_ids).detach()
    baseline = model.get_input_embeddings()(
        torch.tensor([baseline_tokens], device="cuda")
    ).detach()
    attention_mask = torch.ones_like(clean_ids)

    def target_score(inputs_embeds: torch.Tensor) -> torch.Tensor:
        logits = model(
            inputs_embeds=inputs_embeds,
            attention_mask=attention_mask.expand(inputs_embeds.shape[0], -1),
            use_cache=False,
        ).logits[:, -1]
        return logits[:, positive] - logits[:, negative]

    with torch.no_grad():
        embedding_score = target_score(embeddings)[0]
        baseline_score = target_score(baseline)[0]
        direct_score = model(input_ids=clean_ids).logits[0, -1]
        direct_score = direct_score[positive] - direct_score[negative]
    if not torch.isfinite(
        torch.stack((direct_score, embedding_score, baseline_score))
    ).all():
        msg = "The target score is non-finite."
        raise RuntimeError(msg)
    if not torch.allclose(direct_score, embedding_score, atol=1e-4):
        msg = "The input-ID and input-embedding target scores disagree."
        raise RuntimeError(msg)

    attribution, convergence_delta = IntegratedGradients(target_score).attribute(
        embeddings,
        baselines=baseline,
        n_steps=1024,
        method="riemann_middle",
        internal_batch_size=4,
        return_convergence_delta=True,
    )
    token_attribution = attribution.sum(dim=-1)[0]
    delta = float(convergence_delta[0])
    if not torch.isfinite(token_attribution).all() or not math.isfinite(delta):
        msg = "Integrated Gradients produced a non-finite result."
        raise RuntimeError(msg)
    return token_attribution.tolist(), float(baseline_score), delta, space_id


def _patch(
    model: PreTrainedModel,
    clean_ids: torch.Tensor,
    contrast_ids: torch.Tensor,
    position: int,
    targets: tuple[int, int],
) -> float:
    positive, negative = targets
    traced = NNsight(model)
    with torch.no_grad():
        with traced.trace(clean_ids):
            clean_activation = traced.model.layers[0].output.save()
        with traced.trace(contrast_ids):
            traced.model.layers[0].output[:, position, :] = clean_activation[
                :, position, :
            ]
            patched_logits = traced.output.logits.save()
    return float(patched_logits[0, -1, positive] - patched_logits[0, -1, negative])


def main() -> None:
    """Check scoring, explanation, IG completeness, and one residual patch."""
    if not torch.cuda.is_available():
        msg = "The frozen calibration uses a CUDA GPU."
        raise RuntimeError(msg)

    tokenizer = AutoTokenizer.from_pretrained(MODEL, revision=REVISION)
    label_ids = {
        label: tokenizer(label, add_special_tokens=False).input_ids
        for label in ("A", "B")
    }
    if any(len(token_ids) != 1 for token_ids in label_ids.values()):
        msg = f"Target labels changed tokenization: {label_ids}"
        raise ValueError(msg)

    case_tokens = [_tokens_for_case(tokenizer, case) for case in CASES]
    name, question, correct, alternative = CASES[0]
    clean_tokens, contrast_tokens, cue_position = case_tokens[0]
    model = AutoModelForCausalLM.from_pretrained(
        MODEL, revision=REVISION, dtype=torch.float32, attn_implementation="eager"
    ).to("cuda")
    model.eval()
    torch.backends.cuda.matmul.allow_tf32 = False

    clean_ids = torch.tensor([clean_tokens], device="cuda")
    contrast_ids = torch.tensor([contrast_tokens], device="cuda")
    positive, negative = label_ids[correct][0], label_ids[alternative][0]
    targets = (positive, negative)

    with torch.no_grad():
        clean_logits = model(input_ids=clean_ids).logits[0, -1]
        contrast_logits = model(input_ids=contrast_ids).logits[0, -1]
        clean_score = clean_logits[positive] - clean_logits[negative]
        contrast_score = contrast_logits[positive] - contrast_logits[negative]
    if not torch.isfinite(torch.stack((clean_score, contrast_score))).all():
        msg = "The clean or contrast target score is non-finite."
        raise RuntimeError(msg)

    selected = correct if clean_score >= 0 else alternative
    explanation = _explain(model, tokenizer, question, correct, selected)
    token_attribution, baseline_score, convergence_delta, space_id = _attribute(
        model, tokenizer, clean_ids, clean_tokens, targets
    )
    patched_score = _patch(model, clean_ids, contrast_ids, cue_position, targets)
    if not math.isfinite(patched_score):
        msg = "The patched target score is non-finite."
        raise RuntimeError(msg)

    json.dump(
        {
            "case": name,
            "model": MODEL,
            "revision": REVISION,
            "versions": {
                package: metadata.version(package)
                for package in (
                    "torch",
                    "transformers",
                    "captum",
                    "nnsight",
                    "tokenizers",
                )
            },
            "device": torch.cuda.get_device_name(),
            "dtype": "torch.float32",
            "primary_prefix": PRIMARY_PREFIX.format(question=question, cue=correct),
            "target_ids": {
                label: token_ids[0] for label, token_ids in label_ids.items()
            },
            "cue_position": cue_position,
            "space_token_id": space_id,
            "clean_score": float(clean_score),
            "contrast_score": float(contrast_score),
            "baseline_score": float(baseline_score),
            "selected_label": selected,
            "self_explanation": explanation,
            "token_attribution": token_attribution,
            "ig_completeness_delta": convergence_delta,
            "patched_score_layer_0": patched_score,
            "patch_delta_layer_0": patched_score - float(contrast_score),
        },
        sys.stdout,
        indent=2,
    )
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
