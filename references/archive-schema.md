# Archive Schema

Use this structure at the repository root:

```text
.repo-knowledge/
  INDEX.md
  project.md
  inventory/
    repo-map.md
    module-map.json
    code-signals.json
  modules/
    <module>/
      overview.md
  features/
    YYYY-MM-DD-slug/
      request.md
      spec.md
      implementation.md
      verification.md
  decisions/
    0001-title.md
  inbox/
    sync-YYYY-MM-DD-HHMMSS.md
```

## INDEX.md

Purpose: the fast entry point. Keep it under roughly 300 lines.

Required sections:

- Project Snapshot
- How To Read This Archive
- Module Index
- Feature History
- Decisions
- Open Inbox Items

Each entry should include a short summary and a relative link.

## project.md

Purpose: durable repository overview.

Recommended sections:

- Product / Domain
- Runtime Architecture
- Entry Points
- Build And Test Commands
- Cross-Cutting Rules
- Data / API / UI Contracts
- Operational Notes
- Known Risks
- Glossary

## modules/<module>/overview.md

Purpose: where a future agent starts for one subsystem.

Recommended sections:

- Responsibility
- Main Files
- Public Interfaces
- Data Flow
- Existing Behavior
- Extension Points
- Tests
- Related Features
- Related Decisions
- Maintenance Notes

## features/YYYY-MM-DD-slug/

Use a feature folder for both planned and already-implemented requirements.

`request.md` records user/business intent:

- User Request
- Problem / Goal
- In Scope
- Out Of Scope
- Constraints
- Open Questions

`spec.md` records expected behavior:

- Behavior
- Affected Modules
- Inputs / Outputs
- Errors / Edge Cases
- Compatibility
- Acceptance Criteria

`implementation.md` records what changed:

- Summary
- Touched Files
- Design Notes
- Migration / Config Notes
- Follow-Ups

`verification.md` records confidence:

- Automated Checks
- Manual Checks
- Fixtures / Test Data
- Known Gaps

## decisions/

Use decision records for durable why. One decision per file. Prefer append-only updates or superseding records for major reversals.

Template:

```markdown
# NNNN Title

- Status: proposed | accepted | superseded
- Date: YYYY-MM-DD
- Related: links

## Context

## Decision

## Consequences

## Alternatives Considered

## Follow-Up
```

## inbox/

Use inbox notes for raw sync findings that still need curation. Inbox is temporary; canonical information belongs in project, modules, features, or decisions.
