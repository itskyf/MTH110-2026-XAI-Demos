# MTH110 2026 XAI Demos

Research coursework on explainability for generative language models, grounded primarily in Johannes Schneider's _Explainable Generative AI (GenXAI): A Survey, Conceptualization, and Research Agenda_ (2024, arXiv:2404.09554).

Rather than demonstrating many unrelated XAI techniques, this project studies one fixed local generative behavior through several complementary forms of explanation and intervention.

The goal is to understand what each form of evidence can and cannot establish about model behavior, with most of the project effort placed on the underlying mathematical and methodological reasoning rather than software infrastructure.

The canonical sources of truth are:

- [`docs/research/protocol.md`](docs/research/protocol.md) for the scientific question, mathematical definitions, experimental method, interpretation, and reproducibility requirements;
- [`CONTRIBUTING.md`](CONTRIBUTING.md) for GitHub workflow and research-decision handling;
- [`AGENTS.md`](AGENTS.md) for coding-agent constraints.

## Research Overview

Following Schneider's GenXAI framing, this project studies one fixed local generative behavior through four complementary forms of evidence: model self-explanation, Integrated Gradients, controlled input intervention, and activation patching.

The methods are applied to the same frozen experimental behavior so their evidence can be compared without treating them as equivalent explanations or ranking them. The focus is on what each method can support, where their evidence agrees or disagrees, and which assumptions limit the resulting claims.

The core experiment is intentionally small: one small open-weight language model, one controlled-contrast design, and a small frozen set of calibration and research cases. It requires no model training, large-scale benchmarking, or production infrastructure.

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

Run the frozen three-case experiment on a CUDA GPU with:

```shell
pixi run --locked python -m mth110.experiment
```

The command writes the case-level evidence and run metadata to `data/frozen.json`.
After PR review and merge, the finalized JSON is published as an immutable GitHub
Release asset; reruns use a new tag and release.

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the collaboration and verification workflow.

## Repository Map

- `docs/research/protocol.md` — canonical research scope, mathematical definitions, methodology, evaluation, and claim boundaries
- `docs/report/` — scientific report source and interpretation of results
- `src/` — experiment implementation
- `pyproject.toml` and `pixi.lock` — Python dependencies and reproducible experiment environment
- `mise.toml`, `mise.lock`, and `hk.pkl` — development tools and repository checks
- `CONTRIBUTING.md` — collaboration workflow and research-decision handling
- `AGENTS.md` — coding-agent instructions
- GitHub Issues — current work contracts and consequential decisions or findings
- GitHub Milestones — groups of work for research or coursework outcomes
- Pull Requests — review of concrete repository changes and verification

Accepted methods and reproducibility details belong in version-controlled documentation, source, configuration, or recorded experiment outputs rather than chronological Issue logs.

## Reproducibility and Coursework

All numerical results, figures, and tables used in the coursework must come from frozen, reproducible experiment runs. The repository records the code, configuration, exact external model and software revisions, and small result artifacts needed to reproduce reported results without committing model weights or unnecessary large files.

The report and presentation must remain consistent with the frozen experiment, distinguish claims from Schneider (2024), later methodological literature, and this project's observations, and retain weak, negative, ambiguous, or inconsistent results when they occur.
