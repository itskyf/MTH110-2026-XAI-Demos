# Frozen experiment evidence

The canonical evidence is the `frozen.json` asset of release `v1.0.0`
(SHA-256 `23a674f0276156e182c554b81cd3f56fda84b565d726d3efc3319cdd67520728`).
The [generated table, figures, and verbatim self-explanations](../report/evidence.typ)
cover all three frozen cases. The calibration case checks the method locally; the
arithmetic and logic cases are the research cases. All numerical values in that
file and its figures come from the release asset.

## What the recorded run shows

- **Calibration:** The clean input favors the correct A label. Changing only the
  cue to B sharply lowers that preference, although A remains ahead of B. The
  self-explanation gives the factual answer but does not mention the cue. The cue
  has positive signed IG attribution, and restoring its clean activation at
  early layers moves the contrast score toward the clean score. These are
  observations about this fixed prompt pair, not evidence of general knowledge
  or of the explanation's faithfulness.
- **Arithmetic:** The clean score slightly favors A, the *incorrect* label,
  even with the correct B cue. The contrast favors A more strongly. The recorded
  self-explanation was prompted with the selected A label but says B is correct
  and names `Cue: B`; it conflicts with the measured A/B decision. The cue has
  positive signed IG attribution, and early clean-to-contrast patches largely
  reverse the measured input effect. Those interventions show cue sensitivity
  of the fixed score; they do not resolve the self-explanation contradiction or
  show that the model performed the stated calculation.
- **Logic:** The clean input favors correct A; the B-cue contrast favors B. The
  self-explanation gives a valid verbal deduction but omits the cue. The cue's
  signed IG value is positive yet smaller than several other token values.
  Early-layer cue patches move the score back toward the clean behavior, while
  late-layer effects weaken. This is evidence for the specified intervention,
  not a localized reasoning circuit or proof that the verbal deduction caused
  the selected label.

All recorded scores, attributions, patch effects, and diagnostics are finite.
The saved input and patch deltas agree with subtraction from their recorded
scores. The signed token-IG sums agree with the recorded completeness residuals;
the logic residual is visibly larger than the other two, but remains small
relative to its clean-versus-baseline score difference. Completeness assesses
the numerical path integral, not whether the attribution explains the model's
reasoning. No case was removed or adjusted based on its result.

## Assumptions and limits

The shared score compares only the next-token A/B logits. A/B selection is not
an unrestricted generated answer, and a near-zero score in arithmetic should
not be described as confident selection. Input effects apply to the frozen cue
swap only. IG depends on the artificial space-embedding baseline and a straight
path through embeddings that need not represent natural text; signed token sums
can cancel. Patching replaces one cue-position residual-stream output per layer
in the contrast run. Positive effects establish the response to that specific
replacement, not necessity, a complete mechanism, or transfer to other prompts.
The three cases support case-level comparison, not population-level claims or
a ranking of explanation methods.

The interpretation follows the [protocol](protocol.md). Schneider (2024)
provides the conceptual categories and desiderata used there; later IG and
activation-patching literature motivates methodological cautions. The case
observations above come only from this repository's released run. Neither those
sources nor the generated self-explanations supply ground-truth faithfulness.

## Reproduce the evidence

From the repository root, with the configured environment installed:

```shell
bash scripts/fetch_frozen.sh  # only if data/frozen.json is absent
pixi run --locked python scripts/analyze_frozen.py
typst compile docs/report/evidence.typ
```

The downloader uses the fixed release tag and leaves an existing file in place.
The analysis checks its published SHA-256 before producing the table or figures.
The asset records the exact checkpoint, tokenizer revision, library versions,
hardware, prompts, settings, token IDs, and diagnostics; it remains the source
for any later report or seminar excerpt.
