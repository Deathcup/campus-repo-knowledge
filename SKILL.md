---
name: campus-repo-memory
description: Maintain a durable Markdown knowledge archive for an existing code repository, including repo maps, module cards, feature/spec history, decisions, external-change sync notes, and fast agent onboarding. Use when initializing codebase knowledge, starting an incremental requirement, archiving finished work, syncing undocumented code changes, or quickly understanding Java, TypeScript/Vue, C, or other repositories before coding.
---

# Campus Repo Memory

## Purpose

Create and maintain `.repo-knowledge/`, a versioned knowledge layer beside the code. Treat it as docs-as-code for agent memory: it records what the code does, why requirements were shaped that way, where modules live, which decisions matter, and what changed after each feature.

This skill complements SDD, Superpowers, code graphs, and repo maps. Use those tools when helpful, then archive their useful conclusions here so the next agent can recover context from Markdown without repeating full discovery.

## Core Workflow

1. Locate the repository root and `.repo-knowledge/`.
2. If the archive does not exist, run initialization:
   `python <skill>/scripts/repo_knowledge.py init --repo <repo>`
3. For any code task, read in this order:
   - `.repo-knowledge/INDEX.md`
   - `.repo-knowledge/project.md`
   - relevant `.repo-knowledge/modules/*/overview.md`
   - relevant `.repo-knowledge/features/*/*.md`
   - relevant `.repo-knowledge/decisions/*.md`
4. Use the archive to choose code files to inspect. Do not rely on the archive as truth when code disagrees; verify against source.
5. After implementation and validation, run archive/sync and update the Markdown artifacts before finishing.

## Commands

Use the bundled CLI for deterministic file structure and first-pass scanning:

```bash
python <skill>/scripts/repo_knowledge.py init --repo <repo>
python <skill>/scripts/repo_knowledge.py scan --repo <repo> --update
python <skill>/scripts/repo_knowledge.py new-feature --repo <repo> --title "Add log export"
python <skill>/scripts/repo_knowledge.py archive --repo <repo> --feature <feature-id> --summary "Implemented CSV log export" --files "src/logs/exporter.ts,src/logs/api.ts"
python <skill>/scripts/repo_knowledge.py sync --repo <repo> --since HEAD~1
python <skill>/scripts/repo_knowledge.py context --repo <repo> --query "log export conditions"
```

The CLI creates templates and mechanical summaries. Always refine the generated Markdown with the requirement intent, behavioral rules, important tradeoffs, validation evidence, and links to source files.

## New Repository Initialization

Run `init`, then inspect generated files. Upgrade the first pass into useful knowledge:

- Fill `.repo-knowledge/project.md` with product/domain summary, architecture style, runtime entrypoints, build/test commands, coding conventions, and major risks.
- Review `.repo-knowledge/inventory/repo-map.md` and `.repo-knowledge/inventory/module-map.json`.
- For each meaningful module, create or refine `.repo-knowledge/modules/<module>/overview.md`.
- Record non-obvious design choices as `.repo-knowledge/decisions/NNNN-title.md`.
- Add unresolved questions to `.repo-knowledge/inbox/`.

For large repos, use subagents or separate passes by module. Keep the archive small enough to read quickly, but link to exact code files for drill-down.

## Incremental Requirement Flow

When the user gives a new requirement:

1. Run `context --query "<requirement>"` or manually search `.repo-knowledge/`.
2. Read the top matching module and feature docs before inspecting code.
3. Create a feature folder:
   `python <skill>/scripts/repo_knowledge.py new-feature --repo <repo> --title "<short title>"`
4. Write or refine:
   - `request.md`: user intent, constraints, non-goals, open questions.
   - `spec.md`: expected behavior, affected modules, data/API/UI changes, compatibility.
   - `implementation.md`: touched files, design choices, migration notes.
   - `verification.md`: tests run, manual checks, known gaps.
5. Implement normally, with or without SDD/Superpowers.
6. After validation, run `archive` and update `INDEX.md`, module cards, and decisions.

If Superpowers or another SDD tool generated `requirements.md`, `design.md`, `tasks.md`, or similar files, summarize the durable parts into the feature folder. Link to the original artifacts if they remain in the repo; do not duplicate long task lists.

## Sync Existing Changes

Use this when someone changed code without the archive:

1. Run `python <skill>/scripts/repo_knowledge.py sync --repo <repo> --since <base-ref>`.
2. Read the generated `.repo-knowledge/inbox/sync-*.md`.
3. Inspect the changed source files and tests.
4. Decide whether each change updates:
   - project overview
   - module overview
   - a new or existing feature folder
   - a decision record
   - only inventory files
5. Move durable conclusions from `inbox/` into canonical docs, then mark the inbox note handled.

If no base ref is provided, compare the working tree and staged changes. Prefer git history when available.

## Fast Understanding

For quick onboarding, load only the smallest useful set:

1. `INDEX.md`
2. `project.md`
3. `context --query "<task>"`
4. Top matching module cards and feature specs
5. Source files linked from those docs

Ask the archive four questions before coding: Which module owns this? What behavior already exists? What past requirement shaped it? What decisions constrain the change?

## Maintenance Rules

- Keep code-derived facts linked to real files.
- Keep requirement-derived intent in feature folders.
- Keep durable why/tradeoffs in decisions.
- Prefer concise Markdown over exhaustive generated dumps.
- Timestamp sync and archive notes.
- Update indexes whenever adding modules, features, or decisions.
- When code and archive conflict, trust code, fix the archive, and mention the stale doc in the final response.
- Read `references/archive-schema.md` when creating or repairing archive files.
- Read `references/language-hints.md` when scanning Java, TypeScript/Vue, or C repositories.
