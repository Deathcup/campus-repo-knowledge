#!/usr/bin/env python3
"""Maintain a Markdown knowledge archive for a source repository."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

IGNORE_DIRS = {
    ".git",
    ".repo-knowledge",
    "node_modules",
    "dist",
    "build",
    "target",
    ".gradle",
    ".idea",
    ".vscode",
    "__pycache__",
    "coverage",
}

SOURCE_EXTS = {
    ".java",
    ".ts",
    ".tsx",
    ".vue",
    ".js",
    ".jsx",
    ".c",
    ".h",
    ".hpp",
    ".cpp",
    ".cc",
}


def now_stamp() -> str:
    return datetime.now().strftime("%Y-%m-%d-%H%M%S")


def today() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "feature"


def repo_root(path: str | Path) -> Path:
    return Path(path).resolve()


def archive_root(repo: Path) -> Path:
    return repo / ".repo-knowledge"


def rel(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def write_if_missing(path: Path, content: str) -> bool:
    if path.exists():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def run_git(repo: Path, args: list[str]) -> tuple[int, str]:
    try:
        proc = subprocess.run(
            ["git", *args],
            cwd=repo,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except FileNotFoundError:
        return 127, ""
    return proc.returncode, proc.stdout.strip()


def iter_files(repo: Path) -> list[Path]:
    files: list[Path] = []
    for root, dirs, names in os.walk(repo):
        root_path = Path(root)
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith(".cache")]
        for name in names:
            path = root_path / name
            if path.suffix.lower() in SOURCE_EXTS or name in {
                "package.json",
                "pom.xml",
                "build.gradle",
                "settings.gradle",
                "CMakeLists.txt",
                "Makefile",
                "vite.config.ts",
                "tsconfig.json",
            }:
                files.append(path)
    return sorted(files)


def detect_stack(repo: Path, files: list[Path]) -> list[str]:
    names = {f.name for f in files}
    stacks = []
    if {"pom.xml", "build.gradle", "settings.gradle"} & names or (repo / "src/main/java").exists():
        stacks.append("Java")
    if "package.json" in names or (repo / "src/main.ts").exists():
        stacks.append("TypeScript/Vue")
    if {"CMakeLists.txt", "Makefile"} & names or any(f.suffix.lower() in {".c", ".h"} for f in files):
        stacks.append("C")
    return stacks or ["Unknown"]


def guess_module(repo: Path, path: Path) -> str:
    parts = path.relative_to(repo).parts
    if len(parts) >= 4 and parts[:3] == ("src", "main", "java"):
        package_parts = parts[3:-1]
        return package_parts[-1] if package_parts else "java"
    if len(parts) >= 3 and parts[0] == "src" and parts[1] in {"components", "views", "stores", "router", "api", "composables"}:
        return parts[1]
    if len(parts) >= 2 and parts[0] in {"src", "include", "tests"}:
        return parts[1] if len(parts) > 2 else parts[0]
    if len(parts) >= 2:
        return parts[0]
    return "root"


def extract_symbols(path: Path) -> list[str]:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return []
    patterns = [
        r"\b(?:class|interface|enum|record)\s+([A-Za-z_][A-Za-z0-9_]*)",
        r"\b(?:function|const|let|var)\s+([A-Za-z_][A-Za-z0-9_]*)",
        r"\bexport\s+default\s+([A-Za-z_][A-Za-z0-9_]*)",
        r"^\s*([A-Za-z_][A-Za-z0-9_*\s]+)\s+([A-Za-z_][A-Za-z0-9_]*)\s*\([^;]*\)\s*\{",
    ]
    symbols: list[str] = []
    for pattern in patterns:
        for match in re.finditer(pattern, text, flags=re.MULTILINE):
            symbols.append(match.group(match.lastindex or 1).strip())
    return symbols[:12]


def scan_repo(repo: Path) -> dict:
    files = iter_files(repo)
    modules: dict[str, list[dict]] = defaultdict(list)
    for path in files:
        if path.name in {"package.json", "pom.xml", "build.gradle", "settings.gradle", "CMakeLists.txt", "Makefile"}:
            module = "build-config"
        else:
            module = guess_module(repo, path)
        modules[module].append(
            {
                "path": rel(path, repo),
                "ext": path.suffix.lower() or path.name,
                "symbols": extract_symbols(path),
            }
        )
    return {
        "repo": str(repo),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "stacks": detect_stack(repo, files),
        "file_count": len(files),
        "modules": dict(sorted(modules.items())),
    }


def render_repo_map(scan: dict) -> str:
    lines = [
        "# Repo Map",
        "",
        f"- Generated: {scan['generated_at']}",
        f"- Detected stacks: {', '.join(scan['stacks'])}",
        f"- Indexed files: {scan['file_count']}",
        "",
        "## Modules",
        "",
    ]
    for module, entries in scan["modules"].items():
        lines.append(f"### {module}")
        lines.append("")
        for item in entries[:80]:
            symbols = ", ".join(item["symbols"][:8])
            suffix = f" - {symbols}" if symbols else ""
            lines.append(f"- `{item['path']}`{suffix}")
        if len(entries) > 80:
            lines.append(f"- ... {len(entries) - 80} more files")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def module_template(module: str, entries: list[dict]) -> str:
    main_files = "\n".join(f"- `{item['path']}`" for item in entries[:30]) or "- TBD"
    return f"""# {module}

## Responsibility

TBD after reading the code.

## Main Files

{main_files}

## Public Interfaces

TBD.

## Data Flow

TBD.

## Existing Behavior

TBD.

## Extension Points

TBD.

## Tests

TBD.

## Related Features

TBD.

## Related Decisions

TBD.

## Maintenance Notes

Generated first pass. Refine this card after source inspection.
"""


def index_content(scan: dict, features: list[Path] | None = None, decisions: list[Path] | None = None) -> str:
    features = features or []
    decisions = decisions or []
    module_lines = []
    for module, entries in scan["modules"].items():
        module_lines.append(f"- [{module}](modules/{slugify(module)}/overview.md) - {len(entries)} indexed files")
    feature_lines = [f"- [{p.name}](features/{p.name}/request.md)" for p in sorted(features)] or ["- None yet"]
    decision_lines = [f"- [{p.stem}](decisions/{p.name})" for p in sorted(decisions)] or ["- None yet"]
    return f"""# Repo Knowledge Index

## Project Snapshot

- Detected stacks: {", ".join(scan["stacks"])}
- Indexed files: {scan["file_count"]}
- Last scan: {scan["generated_at"]}

## How To Read This Archive

Start with `project.md`, then open the module card and feature history that match the task. Use `inventory/repo-map.md` for code file discovery.

## Module Index

{chr(10).join(module_lines)}

## Feature History

{chr(10).join(feature_lines)}

## Decisions

{chr(10).join(decision_lines)}

## Open Inbox Items

Review `.repo-knowledge/inbox/` for sync notes that still need curation.
"""


def project_template(scan: dict) -> str:
    return f"""# Project Knowledge

## Product / Domain

TBD.

## Runtime Architecture

Detected stacks: {", ".join(scan["stacks"])}.

## Entry Points

TBD.

## Build And Test Commands

TBD.

## Cross-Cutting Rules

TBD.

## Data / API / UI Contracts

TBD.

## Operational Notes

TBD.

## Known Risks

TBD.

## Glossary

TBD.
"""


def feature_templates(title: str) -> dict[str, str]:
    return {
        "request.md": f"""# {title} - Request

- Date: {today()}
- Status: draft

## User Request

TBD.

## Problem / Goal

TBD.

## In Scope

TBD.

## Out Of Scope

TBD.

## Constraints

TBD.

## Open Questions

TBD.
""",
        "spec.md": f"""# {title} - Spec

## Behavior

TBD.

## Affected Modules

TBD.

## Inputs / Outputs

TBD.

## Errors / Edge Cases

TBD.

## Compatibility

TBD.

## Acceptance Criteria

TBD.
""",
        "implementation.md": f"""# {title} - Implementation

## Summary

TBD.

## Touched Files

TBD.

## Design Notes

TBD.

## Migration / Config Notes

TBD.

## Follow-Ups

TBD.
""",
        "verification.md": f"""# {title} - Verification

## Automated Checks

TBD.

## Manual Checks

TBD.

## Fixtures / Test Data

TBD.

## Known Gaps

TBD.
""",
    }


def ensure_archive(repo: Path) -> None:
    if not archive_root(repo).exists():
        raise SystemExit("Archive not found. Run init first.")


def command_init(args: argparse.Namespace) -> None:
    repo = repo_root(args.repo)
    arc = archive_root(repo)
    scan = scan_repo(repo)
    for child in ["inventory", "modules", "features", "decisions", "inbox"]:
        (arc / child).mkdir(parents=True, exist_ok=True)
    write_if_missing(arc / "project.md", project_template(scan))
    write_text(arc / "inventory" / "repo-map.md", render_repo_map(scan))
    write_text(arc / "inventory" / "module-map.json", json.dumps(scan["modules"], indent=2, ensure_ascii=False))
    write_text(arc / "inventory" / "code-signals.json", json.dumps(scan, indent=2, ensure_ascii=False))
    for module, entries in scan["modules"].items():
        write_if_missing(arc / "modules" / slugify(module) / "overview.md", module_template(module, entries))
    write_text(arc / "INDEX.md", index_content(scan, list((arc / "features").glob("*")), list((arc / "decisions").glob("*.md"))))
    print(f"Initialized archive at {arc}")


def command_scan(args: argparse.Namespace) -> None:
    repo = repo_root(args.repo)
    ensure_archive(repo)
    scan = scan_repo(repo)
    if args.update:
        arc = archive_root(repo)
        write_text(arc / "inventory" / "repo-map.md", render_repo_map(scan))
        write_text(arc / "inventory" / "module-map.json", json.dumps(scan["modules"], indent=2, ensure_ascii=False))
        write_text(arc / "inventory" / "code-signals.json", json.dumps(scan, indent=2, ensure_ascii=False))
        for module, entries in scan["modules"].items():
            write_if_missing(arc / "modules" / slugify(module) / "overview.md", module_template(module, entries))
        write_text(arc / "INDEX.md", index_content(scan, list((arc / "features").glob("*")), list((arc / "decisions").glob("*.md"))))
        print("Updated inventory and index.")
    else:
        print(render_repo_map(scan))


def command_new_feature(args: argparse.Namespace) -> None:
    repo = repo_root(args.repo)
    ensure_archive(repo)
    feature_id = f"{today()}-{slugify(args.title)}"
    feature_dir = archive_root(repo) / "features" / feature_id
    for name, content in feature_templates(args.title).items():
        write_if_missing(feature_dir / name, content)
    command_scan(argparse.Namespace(repo=str(repo), update=True))
    print(f"Created feature folder {feature_dir}")


def command_archive(args: argparse.Namespace) -> None:
    repo = repo_root(args.repo)
    ensure_archive(repo)
    feature_dir = archive_root(repo) / "features" / args.feature
    if not feature_dir.exists():
        raise SystemExit(f"Feature folder not found: {feature_dir}")
    files = [f.strip() for f in (args.files or "").split(",") if f.strip()]
    touched = "\n".join(f"- `{f}`" for f in files) or "- TBD"
    impl = feature_dir / "implementation.md"
    existing = impl.read_text(encoding="utf-8") if impl.exists() else f"# {args.feature} - Implementation\n"
    addition = f"""

## Archive Note {datetime.now().isoformat(timespec="seconds")}

{args.summary}

### Touched Files

{touched}
"""
    write_text(impl, existing.rstrip() + addition)
    command_scan(argparse.Namespace(repo=str(repo), update=True))
    print(f"Archived note into {impl}")


def git_changed_files(repo: Path, since: str | None) -> list[str]:
    if since:
        code, out = run_git(repo, ["diff", "--name-only", since, "--"])
    else:
        code, out = run_git(repo, ["status", "--short"])
        if code == 0:
            files = []
            for line in out.splitlines():
                if not line.strip():
                    continue
                payload = line[3:] if len(line) > 2 and line[2] == " " else line[2:]
                if " -> " in payload:
                    payload = payload.split(" -> ", 1)[1]
                files.append(payload.strip())
            return [f for f in files if not f.startswith(".repo-knowledge/")]
    if code != 0:
        return []
    return [line.strip() for line in out.splitlines() if line.strip() and not line.strip().startswith(".repo-knowledge/")]


def command_sync(args: argparse.Namespace) -> None:
    repo = repo_root(args.repo)
    ensure_archive(repo)
    files = git_changed_files(repo, args.since)
    modules = Counter(guess_module(repo, repo / f) for f in files if (repo / f).suffix.lower() in SOURCE_EXTS)
    lines = [
        f"# Sync {now_stamp()}",
        "",
        f"- Base ref: {args.since or 'working tree / staged changes'}",
        f"- Changed files: {len(files)}",
        "",
        "## Changed Files",
        "",
    ]
    lines.extend(f"- `{f}`" for f in files or ["No git changes detected."])
    lines.extend(["", "## Likely Affected Modules", ""])
    lines.extend(f"- {module}: {count} files" for module, count in modules.most_common() or [("TBD", 0)])
    lines.extend(
        [
            "",
            "## Curation Checklist",
            "",
            "- [ ] Inspect changed files and tests.",
            "- [ ] Update module cards for durable behavior changes.",
            "- [ ] Create or update feature folder for requirement intent.",
            "- [ ] Create decision record for durable tradeoffs.",
            "- [ ] Mark this inbox item handled.",
        ]
    )
    path = archive_root(repo) / "inbox" / f"sync-{now_stamp()}.md"
    write_text(path, "\n".join(lines) + "\n")
    command_scan(argparse.Namespace(repo=str(repo), update=True))
    print(f"Wrote sync note {path}")


def command_context(args: argparse.Namespace) -> None:
    repo = repo_root(args.repo)
    ensure_archive(repo)
    arc = archive_root(repo)
    terms = [t.lower() for t in re.findall(r"[\w\u4e00-\u9fff]+", args.query)]
    scores: list[tuple[int, Path, str]] = []
    for path in arc.rglob("*.md"):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        lower = text.lower()
        score = sum(lower.count(term) for term in terms)
        if score:
            snippet = ""
            for line in text.splitlines():
                if any(term in line.lower() for term in terms):
                    snippet = line.strip()
                    break
            scores.append((score, path, snippet))
    for score, path, snippet in sorted(scores, reverse=True)[: args.limit]:
        print(f"{score}\t{rel(path, repo)}\t{snippet}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init")
    init.add_argument("--repo", required=True)
    init.set_defaults(func=command_init)

    scan = sub.add_parser("scan")
    scan.add_argument("--repo", required=True)
    scan.add_argument("--update", action="store_true")
    scan.set_defaults(func=command_scan)

    new_feature = sub.add_parser("new-feature")
    new_feature.add_argument("--repo", required=True)
    new_feature.add_argument("--title", required=True)
    new_feature.set_defaults(func=command_new_feature)

    archive = sub.add_parser("archive")
    archive.add_argument("--repo", required=True)
    archive.add_argument("--feature", required=True)
    archive.add_argument("--summary", required=True)
    archive.add_argument("--files", default="")
    archive.set_defaults(func=command_archive)

    sync = sub.add_parser("sync")
    sync.add_argument("--repo", required=True)
    sync.add_argument("--since")
    sync.set_defaults(func=command_sync)

    context = sub.add_parser("context")
    context.add_argument("--repo", required=True)
    context.add_argument("--query", required=True)
    context.add_argument("--limit", type=int, default=10)
    context.set_defaults(func=command_context)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
