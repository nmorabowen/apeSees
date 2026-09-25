# Agent surface: AGENTS.md only (Phase 1)

Revision 1. Nobody has adversarially reviewed this yet.

**Status:** built on branch `claude/agent-surface`, cut from `origin/main` @ `1ce3f8a`, as a draft
PR. It follows the agent-surface playbook, which was first tried in the Ladruno OpenSees fork
(WP-115). The playbook has three layers:

1. `AGENTS.md`.
2. Short task guides.
3. A lint that runs in CI.

Each layer has to be earned by the repo's own history. This repo earns only layer 1.

## Problem

This repo had no agent-facing documentation at all: no `CLAUDE.md`, no `AGENTS.md`, no
CONTRIBUTING, no docs, no tests, no CI. The README is 18 lines long and stops at the
`pip install` line.

On top of that, agents have a specific way to get this repo wrong. The **name `apeSees` belongs
to two different things**:

- This standalone package, `import apeSees`.
- The OpenSees bridge class inside apeGmsh, `from apeGmsh.opensees import apeSees`.

apeGmsh is far more active than this repo, and so is the user's memory about it: 46 of the 47
memory files that mention "apeSees" are about the apeGmsh class. An agent opening this repo is
therefore primed with facts that do not apply here.

## Phase 0 baseline (measured 2026-09-25)

| Lessons source | Found |
|---|---|
| In-repo gotchas / ledgers / ADRs / post-mortems / CHANGELOG | none |
| Git history | 16 commits, all by the owner, 2025-10-29 → 2025-11-14. Messages are mostly "updates" / "changes". No fix commits that name a bug, no reverts, no PRs |
| User memory (`~/.claude/projects/*/memory/*.md`) | 47 files mention `apeSees`. Only one of them is about this repo: apeGmsh `project_timeseries_wavelet_protocols.md` (FEMA-461 deviation) |
| Recurrences (a written lesson that bit again) | **0** |

To tell the memory files apart, I grepped them for identifiers that exist only in this repo: its
path, its URL, `UniaxialMaterialTester`, `RectangularColumnSection`, `MomentCurvature` and
`ASCE41Protocol`. Only the file named above matched. Every other hit is about the apeGmsh bridge.

**Gate: failed.** There is no lessons archive and no recurrence, so only Phase 1 applies. This is
also the Phase 6 baseline: recurrences = 0 on 2026-09-25.

## Shape

1. **Add `AGENTS.md` and make `CLAUDE.md` the single line `@AGENTS.md`.** No `CLAUDE.md` existed
   before, so there was nothing to move over word for word. `AGENTS.md` supplies what was
   missing:
   - What this repo is, and how it relates to apeGmsh's `apeSees` class. This comes first.
   - The package layout.
   - How to install and verify, including the traps on this machine.
   - Runtime invariants.
   - Known traps.
   - Git and PR rules.

   *Accept:* every path and claim in `AGENTS.md` was checked against the tree or by running it
   (see Results).
2. **Move the one memory lesson about this repo into the repo.** That is the FEMA-461 deviation,
   now under *Known traps* in `AGENTS.md`. The memory file itself is untouched.
   *Accept:* the lesson was re-measured here, not copied: the defaults peak at 0.768 × `max_disp`.
3. **Add `.claude/*` and `!.claude/skills/` to `.gitignore`.** The playbook's worktrees live at
   `.claude/worktrees/`, inside the main checkout. Before this change they showed up there as
   untracked `?? .claude/`, so a `git add -A` in the shared checkout would have picked them up.
   *Accept:* `git check-ignore` ignores `.claude/worktrees/x` and does not ignore
   `.claude/skills/foo/SKILL.md`.

## Rejected approaches

- **Task guides (Phase 2).** All of the history is one 17-day burst that ended ten months ago. It
  contains two kinds of work:
  - Material subclasses: `854ffec`, `8a05dba`, `da52e31`, `1ce3f8a`.
  - Section and moment–curvature refactors.

  A guide's items must point into a lessons archive, and this repo has none, so a guide could
  only restate the code. Revisit when the repo is active again and *Known traps* has grown.
- **Quirk lint (Phase 3).** No lesson has an incident with a pre-fix commit and a fix commit, so
  no rule can pass the mutation gate. I considered three candidates and refused them:
  - *Undeclared third-party import* (`from attr import dataclass`). This could be detected
    mechanically by comparing AST imports with the `pyproject.toml` dependencies. But it was
    never fixed, so there is no fix commit and no mutation pair. It stays a known trap and an
    open question.
  - *FEMA-461 deviation.* A numeric, standards-level lesson that can't be grepped for.
  - *`ops.wipe()` inside the harnesses.* This is the design, not a bug, and `AGENTS.md` documents
    it.
- **Adding a CI workflow.** With no lint and no tests, it would host nothing.
- **Fixing the latent defects below in this PR.** They are production code, and they need review
  first (playbook Phase 5).
- **Writing the full apeGmsh/apeSees history into `AGENTS.md`.** Rejected in favour of a
  comparison table plus a pointer to apeGmsh ADR 0006, which owns that decision.

## Results — verification run on 2026-09-25

| Claim in `AGENTS.md` | How it was checked | Result |
|---|---|---|
| apeGmsh calls this repo legacy and the bridge its successor | Read apeGmsh ADR 0006, ADR 0002 and `architecture/parallel-execution.md` | They name `C:\Users\nmora\Github\apeSees` as the "original research package" / "legacy package" |
| The older clone is the same repo | `git log` / `remote -v` there, read-only | Same `origin`, same HEAD `1ce3f8a` |
| apeGmsh does not import or depend on this package | grep `import apeSees` in apeGmsh `src/` and `pyproject.toml` | Only `from apeGmsh.opensees import apeSees` |
| apeGmsh PR #558 ported the protocols | `gh pr view 558 -R nmorabowen/apeGmsh` | "feat(opensees): wavelet + cyclic-protocol timeSeries primitives", merged 2026-06-07 into `main` |
| The harnesses call `ops.wipe()` | grep, plus a run: node 99 defined, then `Steel02(...).tester.run(ASCE41Protocol(...))` | `getNodeTags()` went from `[99]` to `[]` |
| FEMA461 peak below `max_disp` | `FEMA461Protocol(tag=3).disp` | peak/max = 0.768, 10 amplitudes. ASCE41 peak/max = 1.0 |
| `attrs` is undeclared, and import fails without it | `pip show` Requires for every declared dependency; run with `sys.modules['attr']=None` | No declared dependency requires attrs. `ModuleNotFoundError` at `rectangularColumn.py:4` |
| The wheel ships `examples/` | `pip wheel . --no-deps` (setuptools 80.9.0) in a scratch copy | The wheel contains `examples/*.ipynb` (3 files) |
| An editable install shadows worktrees | `pip show -f apeSees` in `opensees_venv` | Editable location is `C:\Users\nmora\Documents\Github\apeSees` |
| System Python 3.11 can't import openseespy | `python -c "import openseespy.opensees"` | `RuntimeError: Failed to import openseespy on Windows.` |

**Repo gates on new files.** The repo configures no gates: no ruff, pyright, mypy or pytest. This
PR adds no Python files.

## Live incidents — merge order

None. No lint ships, so no rule can have live instances.

The survey did turn up three latent defects in production code. They were **not fixed** here and
need review before any fix:

- `src/apeSees/section/rectangularColumn.py:4` and `src/apeSees/section/rectangularSolidSection.py:4`
  import `attr`, which is not declared. In a clean install that contains only the declared
  dependencies, `import apeSees` fails.
- `src/apeSees/timeseries/protocols.py` (`FEMA461Protocol.__init__`) has two problems:
  - The loop condition `while abs(d) < self.max_disp` means the requested `max_disp` is never
    reached.
  - It runs one cycle per amplitude with `alpha=0.62`, where FEMA 461 §2.2 calls for two cycles
    and about 1.4× growth.
- `pyproject.toml` packaging has two problems:
  - It installs a top-level `examples/` package into site-packages.
  - Its `Bug Tracker` URL points to `github.com/nmorabowen/STKO_to_python/apeSees`.

## Open questions

- Is this repo meant to stay a separate library? apeGmsh ADR 0006 calls apeGmsh the successor.
  If this repo is frozen, a README banner pointing to apeGmsh would help humans as much as
  `AGENTS.md` helps agents.
- Should the defects above be fixed, or left alone because the repo is legacy?
- None of the notebooks in `src/examples/` were re-run.
