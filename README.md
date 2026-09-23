# MTH110 2026 XAI Demos

Research coursework on explainability for generative language models, grounded primarily in Johannes Schneider's _Explainable Generative AI (GenXAI): A Survey, Conceptualization, and Research Agenda_ (2024, arXiv:2404.09554).

Rather than demonstrating many unrelated XAI techniques, this project studies one fixed local generative behavior through several complementary forms of explanation and intervention.

The goal is to understand what each form of evidence can and cannot establish about model behavior, with most of the project effort placed on the underlying mathematical and methodological reasoning rather than software infrastructure.

The canonical sources of truth are:

- [`docs/research/protocol.md`](docs/research/protocol.md) for the scientific question, mathematical definitions, experimental method, interpretation, and reproducibility requirements;
- [`CONTRIBUTING.md`](CONTRIBUTING.md) for GitHub workflow and research-decision handling;
- [`AGENTS.md`](AGENTS.md) for coding-agent constraints.

## Research Framing

Schneider's GenXAI framework separates properties of an explanation from the sources, access requirements, and mechanisms used to obtain it.

Accordingly, this project does not treat self-explanation, feature attribution, behavioral perturbation, and mechanistic intervention as competing entries in a method leaderboard.

They answer different questions about the same model behavior.

The experiment deliberately uses a **focused output scope** and a **single input-output relation**.
It primarily investigates the model and prompt as foundational sources of explanation, while contrasting evidence obtainable from model outputs with evidence requiring gradients or internal activations.

For a fixed input \(x\), the experiment defines one scalar target score \(F(x)\) that represents the generative behavior being studied.
For the preferred next-token contrast,

\[
F(x) = z_{y^+}(x) - z_{y^-}(x),
\]

where \(z_{y^+}\) and \(z_{y^-}\) are the logits of the contrasted target tokens.

The same \(F\) is then used throughout the experiment.
This common target is what makes the different analyses comparable without pretending that they are the same kind of explanation.

## Experiment

```text
controlled input contrast
        ↓
fixed model behavior and target score F
        │
        ├── model self-explanation
        │       What does the model say mattered?
        │
        ├── Integrated Gradients
        │       Which input dimensions are F sensitive to
        │       along the defined attribution path?
        │
        ├── controlled input intervention
        │       How much does F change under the predefined
        │       finite input contrast?
        │
        └── activation patching
                How does F change under a specified
                intervention on an internal activation?
        ↓
compare agreement, disagreement, assumptions, and claim boundaries
```

Integrated Gradients is treated as a path-based attribution method rather than as a causal explanation.
Its numerical implementation is checked using the expected completeness relation

$$
\sum_i IG_i \approx F(e) - F(e'),
$$

where \(e\) and \(e'\) are the input representation and the frozen baseline.

The controlled input contrast measures a finite behavioral effect,

$$
\Delta F_{\mathrm{input}}
=
F(x^{\mathrm{contrast}})
-
F(x^{\mathrm{clean}}),
$$

while activation patching asks a different causal question by intervening on a selected internal activation and measuring the resulting change in the same target score.

The project therefore preserves several important distinctions:

$$
\text{plausibility} \neq \text{faithfulness},
$$

$$
\text{attribution} \neq \text{causal mechanism},
$$

and

$$
\text{agreement between explanations} \neq \text{proof of a complete mechanism}.
$$

Exact method definitions, intervention semantics, frozen experimental choices, and interpretation limits belong to the [research protocol](docs/research/protocol.md).

## Scope

The core experiment is intentionally small: one small open-weight language model, one controlled-contrast design, one common target-score definition, and a small frozen set of calibration and research cases.

No model training or fine-tuning is required.

The project is not intended to be a general XAI benchmark, a catalogue of explanation methods, or a production GenAI system.
Additional techniques are included only when they directly serve the research question.

The complete scope and explicit non-scope are defined in [`docs/research/protocol.md`](docs/research/protocol.md).

## Reproducibility

Every numerical result, figure, and table used in the coursework report or presentation must come from an actual reproducible experiment run.

The repository records the code, configuration, external model revisions, and small result artifacts needed to reproduce reported results without committing model weights or unnecessary large files.

The exact reproducibility record and protocol-freeze requirements are defined in [`docs/research/protocol.md`](docs/research/protocol.md).

Live work status, ownership, dependencies, research decisions, and milestone progress are tracked through GitHub rather than duplicated in repository documentation.
See [`CONTRIBUTING.md`](CONTRIBUTING.md).

## Development

The Python environment is managed with Pixi, while repository development tools are versioned with mise.

Install the configured tools and environment:

```shell
mise install
pixi install
```

Run the repository checks with:

```shell
hk check --all
hk run pre-commit
```

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the collaboration and verification workflow.

## Repository Map

- `docs/research/protocol.md` — canonical scientific protocol and mathematical definitions
- `src/` — experiment implementation
- `pyproject.toml` — Python project, dependencies, and Pixi configuration
- `pixi.lock` — locked Python/software environment
- `mise.toml` and `mise.lock` — development-tool versions
- `CONTRIBUTING.md` — GitHub workflow and research-decision process
- `AGENTS.md` — repository-wide instructions for coding agents

GitHub Issues track scoped work and research decisions that require independent tracking.
GitHub Milestones group work around meaningful research or coursework outcomes.

## Coursework

This repository is the reproducible source workspace for the coursework.

The report and presentation must remain consistent with the frozen experiment and distinguish clearly between:

- claims from Schneider (2024);
- claims from later methodological literature;
- observations produced by this project's experiments.

Reported conclusions must reflect the observed results, including weak, negative, ambiguous, or inconsistent cases.
