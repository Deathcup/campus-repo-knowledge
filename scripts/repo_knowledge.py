#!/usr/bin/env python3
"""为代码仓维护可版本化的中文知识库。"""

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
    text = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "需求"


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
        "# 代码仓地图",
        "",
        f"- 生成时间：{scan['generated_at']}",
        f"- 识别技术栈：{', '.join(scan['stacks'])}",
        f"- 已索引文件：{scan['file_count']}",
        "",
        "## 模块",
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
            lines.append(f"- ……另有 {len(entries) - 80} 个文件")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def module_template(module: str, entries: list[dict]) -> str:
    main_files = "\n".join(f"- `{item['path']}`" for item in entries[:30]) or "- 待补充"
    return f"""# {module}

## 模块职责

待阅读源码后补充。

## 关键文件

{main_files}

## 对外接口

待补充。

## 数据流

待补充。

## 现有行为

待补充。

## 扩展点

待补充。

## 测试

待补充。

## 关联需求

待补充。

## 关联决策

待补充。

## 维护注意事项

这是自动生成的第一版。阅读源码和测试后补全，并给出相对路径作为证据。
"""


def index_content(scan: dict, features: list[Path] | None = None, decisions: list[Path] | None = None) -> str:
    features = features or []
    decisions = decisions or []
    module_lines = []
    for module, entries in scan["modules"].items():
        module_lines.append(f"- [{module}](modules/{slugify(module)}/overview.md) - 已索引 {len(entries)} 个文件")
    feature_lines = [f"- [{p.name}](features/{p.name}/request.md)" for p in sorted(features)] or ["- 暂无"]
    decision_lines = [f"- [{p.stem}](decisions/{p.name})" for p in sorted(decisions)] or ["- 暂无"]
    return f"""# 代码仓知识索引

## 项目快照

- 识别技术栈：{", ".join(scan["stacks"])}
- 已索引文件：{scan["file_count"]}
- 最近扫描：{scan["generated_at"]}

## 阅读顺序

先读 `project.md`，再打开与当前任务相关的模块卡、需求历史和决策。需要定位源码时查阅 `inventory/repo-map.md`。

## 模块索引

{chr(10).join(module_lines)}

## 需求历史

{chr(10).join(feature_lines)}

## 关键决策

{chr(10).join(decision_lines)}

## 待处理同步项

检查 `.repo-knowledge/inbox/`，将尚未整理的同步记录归入正式知识文档。
"""


def project_template(scan: dict) -> str:
    return f"""# 项目知识

## 产品与领域

待补充。

## 运行架构

识别到的技术栈：{", ".join(scan["stacks"])}。

## 入口

待补充。

## 构建与测试命令

待补充。

## 横切规则

待补充。

## 数据、API 与 UI 契约

待补充。

## 运行与运维说明

待补充。

## 已知风险

待补充。

## 术语表

待补充。
"""


def feature_templates(title: str) -> dict[str, str]:
    return {
        "request.md": f"""# {title} - 需求

- 日期：{today()}
- 状态：草稿

## 用户需求

待补充。

## 问题与目标

待补充。

## 范围内

待补充。

## 非目标

待补充。

## 约束

待补充。

## 待确认问题

待补充。
""",
        "spec.md": f"""# {title} - 规格

## 预期行为

待补充。

## 受影响模块

待补充。

## 输入与输出

待补充。

## 异常与边界

待补充。

## 兼容性

待补充。

## 验收条件

待补充。
""",
        "implementation.md": f"""# {title} - 实现

## 实现摘要

待补充。

## 变更文件

待补充。

## 设计说明

待补充。

## 迁移与配置

待补充。

## 后续事项

待补充。
""",
        "verification.md": f"""# {title} - 验证

## 自动化检查

待补充。

## 手动检查

待补充。

## 测试数据

待补充。

## 已知缺口

待补充。
""",
    }


def ensure_archive(repo: Path) -> None:
    if not archive_root(repo).exists():
        raise SystemExit("未找到知识库，请先执行 init。")


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
    print(f"已在 {arc} 初始化知识库")


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
        print("已更新代码清单和索引。")
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
    print(f"已创建需求目录 {feature_dir}")


def command_archive(args: argparse.Namespace) -> None:
    repo = repo_root(args.repo)
    ensure_archive(repo)
    feature_dir = archive_root(repo) / "features" / args.feature
    if not feature_dir.exists():
        raise SystemExit(f"未找到需求目录：{feature_dir}")
    files = [f.strip() for f in (args.files or "").split(",") if f.strip()]
    touched = "\n".join(f"- `{f}`" for f in files) or "- 待补充"
    impl = feature_dir / "implementation.md"
    existing = impl.read_text(encoding="utf-8") if impl.exists() else f"# {args.feature} - 实现\n"
    addition = f"""

## 归档记录 {datetime.now().isoformat(timespec="seconds")}

{args.summary}

### 变更文件

{touched}
"""
    write_text(impl, existing.rstrip() + addition)
    command_scan(argparse.Namespace(repo=str(repo), update=True))
    print(f"已将归档记录写入 {impl}")


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
        f"# 同步记录 {now_stamp()}",
        "",
        f"- 比较基线：{args.since or '工作区与暂存区改动'}",
        f"- 变更文件数：{len(files)}",
        "",
        "## 变更文件",
        "",
    ]
    lines.extend(f"- `{f}`" for f in files or ["未检测到 Git 变更。"])
    lines.extend(["", "## 可能受影响的模块", ""])
    lines.extend(f"- {module}：{count} 个文件" for module, count in modules.most_common() or [("待确认", 0)])
    lines.extend(
        [
            "",
            "## 整理清单",
            "",
            "- [ ] 检查变更文件与相关测试。",
            "- [ ] 将长期行为变化更新到模块卡。",
            "- [ ] 为需求意图创建或更新需求目录。",
            "- [ ] 为长期取舍创建决策记录。",
            "- [ ] 记录推断内容、置信度和待确认项。",
            "- [ ] 标记本同步项的处理结果。",
        ]
    )
    path = archive_root(repo) / "inbox" / f"sync-{now_stamp()}.md"
    write_text(path, "\n".join(lines) + "\n")
    command_scan(argparse.Namespace(repo=str(repo), update=True))
    print(f"已生成同步记录 {path}")


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
