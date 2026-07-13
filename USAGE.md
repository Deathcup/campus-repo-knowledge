# Campus Repo Memory Skill - Usage Guide

## What Was Built

Skill path:

`D:\codex\repo-knowledge-archive-project\campus-repo-memory`

Validation sample repo:

`D:\codex\repo-knowledge-archive-project\validation\sample-repo`

The skill creates and maintains a `.repo-knowledge/` folder inside a code repository. This folder is a durable Markdown archive for:

- codebase overview and module locations
- requirement intent and feature specs
- implementation notes and validation evidence
- decision records
- external code-change sync notes
- fast context lookup before future coding

## Research Notes

I borrowed from several established ideas, but intentionally did not copy any single system:

- ADRs: use small Markdown decision records to preserve context, consequences, and durable "why".
- Aider repo map: keep a concise repository map so an agent can choose which files to inspect.
- Spec-driven tools: keep requirement/spec/implementation/verification artifacts, but make them optional archives instead of forcing full SDD.
- Memory-bank style project docs: maintain project/module/active-context files as versioned Markdown, but avoid a single giant context dump.

Useful sources:

- https://github.com/architecture-decision-record/architecture-decision-record
- https://aider.chat/docs/repomap.html
- https://github.com/github/spec-kit

## Installation

To make Codex discover the skill automatically, copy or move this folder into your Codex skills directory:

`C:\Users\Jiang\.codex\skills\campus-repo-memory`

For local testing without installing, explicitly tell Codex:

`Use $campus-repo-memory at D:\codex\repo-knowledge-archive-project\campus-repo-memory ...`

## Scenario 1: New Repository Initialization

Run:

```powershell
python D:\codex\repo-knowledge-archive-project\campus-repo-memory\scripts\repo_knowledge.py init --repo <repo>
```

Then ask the agent to refine:

```text
Use $campus-repo-memory to initialize knowledge for this repository. Read the generated .repo-knowledge files, inspect the important modules, and replace TBDs with accurate project/module knowledge.
```

Expected output inside the repo:

```text
.repo-knowledge/
  INDEX.md
  project.md
  inventory/
  modules/
  features/
  decisions/
  inbox/
```

## Scenario 2: Incremental Requirement Archive

Before coding:

```powershell
python <skill>\scripts\repo_knowledge.py context --repo <repo> --query "日志模块 导出"
python <skill>\scripts\repo_knowledge.py new-feature --repo <repo> --title "Add log export"
```

During or after coding, fill:

```text
.repo-knowledge/features/YYYY-MM-DD-add-log-export/request.md
.repo-knowledge/features/YYYY-MM-DD-add-log-export/spec.md
.repo-knowledge/features/YYYY-MM-DD-add-log-export/implementation.md
.repo-knowledge/features/YYYY-MM-DD-add-log-export/verification.md
```

After validation:

```powershell
python <skill>\scripts\repo_knowledge.py archive --repo <repo> --feature YYYY-MM-DD-add-log-export --summary "Implemented CSV export for logs." --files "src/api/logs.ts,src/logs/exporter.ts"
```

If Superpowers or another SDD workflow produced specs, summarize the durable parts into this feature folder and link to the original files.

## Scenario 3: Sync Undocumented Changes

When someone changed code without using the skill:

```powershell
python <skill>\scripts\repo_knowledge.py sync --repo <repo> --since HEAD~1
```

Then read the generated:

```text
.repo-knowledge/inbox/sync-YYYY-MM-DD-HHMMSS.md
```

Curate its findings into module cards, feature history, project overview, or decisions. The inbox is a staging area, not the final home.

## Scenario 4: Fast Agent Understanding

For a new task, tell the agent:

```text
Use $campus-repo-memory. First read .repo-knowledge/INDEX.md and run context for my requirement. Then inspect only the linked module docs and source files before designing the change.
```

The agent should answer these before coding:

- Which module owns this?
- What behavior already exists?
- What past requirement shaped it?
- What decisions constrain the change?

## Validation Performed

I tested the skill against a sample mixed-language repo containing:

- TypeScript API/store files
- Java log service
- C header/source export function

Commands verified:

```powershell
python <skill>\scripts\repo_knowledge.py init --repo <sample>
python <skill>\scripts\repo_knowledge.py new-feature --repo <sample> --title "Add log export"
python <skill>\scripts\repo_knowledge.py archive --repo <sample> --feature 2026-07-13-add-log-export --summary "Implemented CSV log export for filtered logs and documented acceptance criteria." --files "src/api/logs.ts,src/c/log_export.c,include/log_export.h"
python <skill>\scripts\repo_knowledge.py sync --repo <sample>
python <skill>\scripts\repo_knowledge.py context --repo <sample> --query "exportLogs"
python C:\Users\Jiang\.codex\skills\.system\skill-creator\scripts\quick_validate.py <skill>
```

The validation caught and fixed two issues:

- Java packages were initially grouped too coarsely as `com`; now `com.demo.logs` maps to `logs`.
- `git status --short` parsing could drop the first path character; now it parses changed paths robustly and filters `.repo-knowledge/` noise.
