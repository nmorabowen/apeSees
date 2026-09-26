# apeSees — working rules for agents

## Which "apeSees" is this? Read this first

Two different things share the name.

| | **This repo** (`nmorabowen/apeSees`) | **apeGmsh's `apeSees` class** |
|---|---|---|
| What it is | A standalone Python package: `import apeSees` | A class inside apeGmsh: `from apeGmsh.opensees import apeSees`, used as `apeSees(fem)` |
| What it does | Drives openseespy **live** for small studies: uniaxial material cyclic/backbone tests, fiber sections and moment–curvature, cyclic loading protocols | A typed OpenSees bridge fed by apeGmsh's `FEMData` mesh snapshot. It writes Tcl/Python decks or runs openseespy |
| Code | `src/apeSees/` in this repo | `src/apeGmsh/opensees/apesees.py` in `nmorabowen/apeGmsh` |
| State | v0.1.0. Last commit 2025-11-14. No tests, no CI | Under active development |

**How they relate.** This record comes from apeGmsh itself. apeGmsh ADR 0006
(`src/apeGmsh/opensees/architecture/decisions/0006-class-name-apesees.md`) calls this repo "the
original research package" and "legacy package". It named the bridge class after this repo and
calls that class the "canonical successor". apeGmsh ADR 0002 used this repo's
`materials/base.py` as a legacy reference. apeGmsh PR #558 ported this repo's cyclic protocols and
corrected FEMA-461 along the way (see *Known traps*). apeGmsh does not import or depend on this
package.

What this means for your task:

- A task that mentions `apeSees(fem)`, `FEMData`, `g.mesh`, emitters, Tcl/Py decks, `Results` or
  `model.h5` belongs in **apeGmsh**, not here.
- apeGmsh ADRs refer to this repo by the local path `C:\Users\nmora\Github\apeSees`. That is an
  older clone of this same repo (same `origin`). The working clone is
  `C:\Users\nmora\Documents\Github\apeSees`. Leave the older clone alone.
- ADR 0006 treats apeGmsh as the successor. Before you add a new feature here, ask the owner
  whether it belongs in apeGmsh instead.

## Layout

- `src/apeSees/materials/` contains:
  - `Material`, a generic factory for `ops.uniaxialMaterial` (type, tag, then parameters in
    OpenSees order), with one subclass per OpenSees material.
  - `UniaxialMaterialTester`, a one-truss test harness, and `MaterialTestResult`.
- `src/apeSees/section/` contains:
  - The `Section` ABC and `GeneralFiberSection` (patches plus fibers).
  - The rectangular sections.
  - `MomentCurvature`, whose solvers live under `.solve`.
  - `FiberMapper`, `NeuralMomentCurvatureTrainer` and the result classes.
- `src/apeSees/timeseries/` contains:
  - The `TimeSeries` ABC, with `build` / `plot` / `to_dataclass`.
  - The Linear, Constant and Path series.
  - The ASCE-41, Modified ATC-24 and FEMA-461 protocols.
- `src/apeSees/utilities/` contains `AttrDict`.
- `src/examples/` holds notebooks plus `.npz`/`.out` data.

Don't list classes here. The `__all__` in each subpackage's `__init__.py` is the inventory. The
top-level `apeSees/__init__.py` re-exports only some of them. For example, `Steel02` and
`Concrete02` are only in `apeSees.materials`.

## Install, run, verify

- Install with `pip install -e .`. The project uses setuptools, a `src/` layout and
  `requires-python >= 3.8`. Its declared dependencies are numpy, matplotlib, openseespy, pandas
  and scipy.
- **There is no test suite, no CI, and no lint or type-checker config.** Never report "tests
  pass". The checks available are:
  - The import smoke test, `python -c "import apeSees"`.
  - The notebooks in `src/examples/`.
  - Small scripts you write yourself. Keep those in your scratchpad, not the repo.
- On the maintainer's Windows machine:
  - The system Python 3.11 cannot import openseespy (`openseespy` and `openseespywin` versions
    don't match).
  - Use `C:\Users\nmora\venv\opensees_venv\Scripts\python.exe` (Python 3.12) instead. That venv
    has apeSees **editable-installed from the main checkout**. From a worktree, set
    `PYTHONPATH=src`, or you will import the main checkout's code.
  - For headless runs, set `MPLBACKEND=Agg`.

## Runtime invariants (true of the code today)

- **The harnesses own openseespy's single process-global domain.** Each of these calls
  `ops.wipe()`:
  - `UniaxialMaterialTester.run`, before and after the run.
  - Every `MomentCurvature.solve.*` method.
  - `FiberMapper`.
  - `NeuralMomentCurvatureTrainer`.

  So any model you built earlier in the process is gone afterwards. Never call these in the
  middle of your own analysis.
- **Harness tags are hard-coded.**
  - The tester uses nodes 1–2, element 1 and pattern 1.
  - Moment–curvature uses nodes 1–2, element 200, timeSeries 500 (axial load) and 501 (the
    curvature ramp, or the default protocol in `cyclic`), and patterns 600/601.
  - A protocol you pass to the cyclic solver is built under its own tag, so don't give it
    tag 500.
- **`build()` is how every object talks to OpenSees.** `Material`, `Section` and `TimeSeries`
  objects all define it, and it returns the tag. A section's `build()` also builds all of its
  materials.
- **Each material carries its own strain limits.** They are `max_tensile_strain` and
  `max_compressive_strain`, and the default of ±1e10 means no limit. The moment–curvature solvers
  that check limits use the tightest one across `section.get_materials()`.
- **Units are not enforced.** Docstrings and plot labels assume N–mm (MPa).

## Known traps (this is the lessons archive, so add new ones here)

- **`FEMA461Protocol` does not follow FEMA 461.** It is in `src/apeSees/timeseries/protocols.py`.
  - It runs one cycle per amplitude, with a default `alpha=0.62`.
  - Its loop stops before reaching `max_disp`. With the defaults it produces 10 amplitudes, and
    the peak is only about 0.77 × `max_disp`.
  - apeGmsh's port (PR #558) follows FEMA 461 §2.2 instead: two cycles per amplitude and about
    1.4× growth (`alpha=0.4`). This file was never changed.
  - The ASCE-41 and Modified ATC-24 protocols do end at `max_disp`.
  - Sources: apeGmsh project memory (2026). The peak was re-measured here on 2026-09-25.
- **`attrs` is imported but not declared.** `section/rectangularColumn.py:4` and
  `section/rectangularSolidSection.py:4` both do `from attr import dataclass`. `pyproject.toml`
  doesn't declare `attrs`, and none of the declared dependencies pull it in. Without `attrs`
  installed, `import apeSees` fails with `ModuleNotFoundError`.
- **The wheel ships a top-level `examples/` package.** `packages = {find = ...}` in
  `pyproject.toml` includes namespace packages. Together with the `*.ipynb` package-data rule,
  this installs the three notebooks as `site-packages/examples/`. This was checked with
  setuptools 80.9.

## Git and PRs

- The default branch is `main`. It is unprotected, there is no CI, and there were no PRs before
  the agent-surface one. `origin/nmb_WIP` points at the same commit as `main`. `origin/pxpalacios`
  is an older branch whose commits are already in `main`.
- Work in a worktree on a new branch cut from a fresh `origin/main`. Don't switch branches or
  commit in the shared checkout.
- Open every PR with `--base main`, even when PRs depend on each other. Stacking a PR on another
  feature branch strands its commits.
- Plans and design notes go in `docs/`. `docs/agent-surface.md` explains why this repo has
  `AGENTS.md` but no task guides and no lint yet.
- `.claude/` is session scratch and is ignored by git. Only `.claude/skills/` would be tracked,
  and none exist yet.
