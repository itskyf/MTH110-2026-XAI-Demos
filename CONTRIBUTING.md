# Contributing

MTH110-2026-XAI-Demos is a small research coursework project.
Keep collaboration scientifically defensible, reproducible, reviewable, and lightweight.

## Work Model

Repository work follows:

```text
Issue → Pull Request → Merge
```

Use GitHub's native work-management features rather than maintaining parallel planning systems.

Each primitive has one purpose:

- **Milestone** — groups work contributing to a meaningful research or deliverable outcome. It is not a sprint or workflow status.
- **Issue** — an independently trackable unit of research, implementation, experiment, or decision work.
- **Sub-issue** — decomposes a parent Issue only when separate implementation, ownership, review, or completion is useful.
- **Dependency** — represents a real blocking relationship between Issues.
- **Assignee** — identifies current ownership.
- **Label** — classifies work when repeated filtering is useful.
- **Pull Request** — reviews concrete changes to code, configuration, experiment definitions, or durable documentation.

Do not create an Issue merely to mirror a Milestone.

Do not duplicate status, milestone, ownership, priority, parent-child, or dependency information in Issue bodies, labels, or repository documentation when GitHub already represents it natively.

Do not introduce a Project board, custom workflow state, or additional planning system without a demonstrated recurring need.

Use milestone due dates only for actual deadlines.

## Issues

Use an Issue before substantive implementation, experimental work, or a consequential research decision that needs independent tracking.

An Issue should provide enough information to establish:

- why the work or decision is needed;
- what is in scope;
- observable outputs, evidence, or acceptance criteria that determine completion.

State explicit non-scope only when it prevents meaningful ambiguity.

Use the repository Issue template when creating normal work items.
The template provides the presentation structure; this document defines the workflow semantics.

Use GitHub metadata and native relationships for assignees, milestones, sub-issues, and dependencies rather than repeating them in the Issue body.

Create sub-issues only when decomposition provides practical value, such as independent ownership, review, or completion.
Do not create hierarchies for work that can be completed coherently in one Issue.

Small typo or formatting corrections do not require an Issue.

## Work Lifecycle

Work generally follows:

```text
Frame → Execute ↔ Inspect → Close
```

- **Frame:** establish sufficient scope, evidence requirements, and completion criteria.
- **Execute:** implement, run experiments, or gather the required evidence.
- **Inspect:** review outputs, representative cases, failures, measurements, and relevant repository changes.
- **Close:** merge required repository changes and close the Issue when its completion criteria are satisfied.

Execution and inspection may repeat as necessary.

A separate decision step is not required for ordinary implementation choices.
When work exposes a consequential methodological choice, resolve it using the research-decision process below.

Work may proceed in parallel whenever no real dependency blocks it.

## Research Decisions

The current research method is defined in [`docs/research/protocol.md`](docs/research/protocol.md).

The protocol is the source of truth for the research question, experimental behavior, target score, controlled contrasts, explanation and intervention methods, evaluation procedure, claim boundaries, and final experimental scope.

A change is a **research decision** when it changes the scientific meaning of the experiment rather than only its implementation.

Examples include changes to:

- the research question or claims being investigated;
- the selected model or checkpoint when the change can affect reported behavior;
- the frozen controlled prompt pairs or case set;
- the target tokens or mathematical definition of the target score;
- the self-explanation elicitation procedure;
- the Integrated Gradients baseline, path, numerical procedure, or attribution aggregation rule;
- the definition of the controlled input intervention;
- the activation location, patch direction, or intervention scope;
- inference settings that materially affect reported results;
- an evaluation procedure, reported quantity, or criterion used to support a scientific claim.

Ordinary implementation choices that preserve these scientific semantics are not separate research decisions.
Examples include refactoring code, changing file organization, replacing an equivalent library helper, improving plotting code, or changing caching strategy without changing computed quantities.

When a research decision requires independent tracking:

1. discuss the alternatives and relevant evidence in an Issue;
2. update the protocol, configuration, code, or other durable source of truth as appropriate;
3. merge the accepted change through a Pull Request;
4. rerun any reported experiment whose scientific interpretation is affected;
5. close the Issue when its completion criteria are satisfied.

Do not create a separate decision-tracking Issue when the current Issue already exists specifically to resolve that decision.

The closed Issue preserves discussion and rationale.
The repository preserves the accepted method.

### Protocol freeze

The feasibility study may motivate changes to methodological choices before the final experiment is frozen.

Once the final protocol is frozen, do not change a scientific choice on an individual case merely because the resulting explanation, attribution, or intervention effect is weak, ambiguous, or undesirable.

A post-freeze methodological change requires an explicit protocol amendment and rerunning the affected reported results.

Negative, weak, ambiguous, and inconsistent results are valid experimental outcomes.

## During Work

Keep the Issue body as the current work contract, not a chronological log.

If scope materially changes, update the Issue body and leave a concise comment explaining the change.

If independent follow-up work is discovered, create another Issue only when it needs separate tracking.
Use a sub-issue or dependency relationship when that relationship is real.

Use Issue comments for matters outside the proposed diff, such as:

- scope or methodological discussion;
- experimental evidence;
- blockers;
- significant findings or handoff information.

Use Pull Request review comments for findings about the proposed diff.

Do not create parallel `plan.md`, `status.md`, research-log, ADR, or similar tracking systems without a demonstrated need.

## Pull Requests

Prefer one coherent concern per Pull Request.

Use the repository Pull Request template.
A Pull Request should make clear:

- what changed and why;
- how the change was verified;
- whether the research method changed;
- whether previously reported results must be rerun;
- any effect on reproducibility;
- the related Issue, when applicable.

For experiment-related Pull Requests, verification should check the relevant scientific behavior rather than only whether the code executes.

Depending on the change, this may include confirming that:

- the frozen target score is computed as defined in the protocol;
- controlled clean/contrast cases remain unchanged;
- Integrated Gradients satisfies the expected numerical sanity checks;
- intervention direction and activation location match the frozen experiment;
- reported tables or figures are generated from recorded experimental outputs.

Do not add verification requirements that are unrelated to the changed work.

Use `Closes #N` only when merging the Pull Request fully completes that Issue.
Otherwise, reference the Issue without a closing keyword.

Use draft Pull Requests when early review is useful.
Mark a Pull Request ready when the relevant work and verification are complete.

Merge is the point at which repository changes become canonical.

## Research Reproducibility

The reproducibility requirements for the experiment are defined in [`docs/research/protocol.md`](docs/research/protocol.md).

Repository work should preserve enough information to rerun every result used in the report or presentation without constructing additional infrastructure.

In particular:

- record exact external model and software revisions when they materially affect the experiment;
- keep the frozen prompts, target definitions, and experiment configuration in version-controlled files;
- preserve the commands needed to reproduce final runs;
- persist the small numerical outputs needed to regenerate reported figures and tables when recomputation would otherwise obscure the exact reported run;
- keep figures, tables, screenshots, and numerical claims traceable to actual experiment outputs.

Use the simplest appropriate machine-readable representation for persisted experimental data.

Do not require a general manifest, provenance database, experiment-tracking service, or data-lineage framework when ordinary source files, configuration, lockfiles, commands, and small result artifacts already provide sufficient reproducibility.

Do not commit model weights, caches, unnecessary large datasets, or generated artifacts that are not required to reproduce reported coursework results.

Do not alter prompts, expected behavior, target definitions, attribution settings, intervention definitions, methodological criteria, or evaluation procedures merely to make an implementation or experiment appear successful.

The report and presentation must distinguish:

- claims taken from Schneider (2024);
- claims from later methodological literature;
- observations obtained from this repository's experiments.

## Development Tooling

See [`README.md`](README.md) for environment setup and local usage.

Run repository checks with:

```shell
hk check --all
hk run pre-commit
```

Use `hk fix --all` when applying supported automatic fixes.

Treat configured checks as constraints to satisfy.
Fix root causes rather than weakening checks or adding suppressions solely to make a change pass.
