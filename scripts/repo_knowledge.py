#!/usr/bin/env python3
"""为代码仓维护分层、可版本化、面向人和 Agent 的中文知识库。"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

SCHEMA_VERSION = 2
IGNORE_DIRS = {
    ".git", ".repo-knowledge", "node_modules", "dist", "build", "target",
    ".gradle", ".idea", ".vscode", "__pycache__", "coverage", "vendor",
}
SOURCE_EXTS = {
    ".java", ".kt", ".ts", ".tsx", ".vue", ".js", ".jsx", ".py",
    ".go", ".rs", ".c", ".h", ".hpp", ".cpp", ".cc", ".cs",
}
MANIFESTS = {
    "package.json", "pom.xml", "build.gradle", "build.gradle.kts", "settings.gradle",
    "settings.gradle.kts", "Cargo.toml", "go.mod", "pyproject.toml", "requirements.txt",
    "CMakeLists.txt", "Makefile", "meson.build", "vite.config.ts", "vite.config.js",
}
FRONTEND_HINTS = {"frontend", "front-end", "web", "ui", "client", "admin", "h5", "app"}
BACKEND_HINTS = {"backend", "back-end", "server", "service", "services", "api", "gateway"}
LAYER_DIRS = {
    "controller", "controllers", "service", "services", "repository", "repositories",
    "dao", "mapper", "mappers", "entity", "entities", "model", "models", "domain",
    "api", "apis", "view", "views", "page", "pages", "component", "components",
    "store", "stores", "composable", "composables", "handler", "handlers", "route", "routes",
}


def now_stamp() -> str:
    return datetime.now().strftime("%Y-%m-%d-%H%M%S")


def today() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "-", text)
    return re.sub(r"-+", "-", text).strip("-") or "未命名"


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
            ["git", *args], cwd=repo, text=True, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, check=False,
        )
    except FileNotFoundError:
        return 127, ""
    return proc.returncode, proc.stdout.strip()


def walk_source_files(root: Path, repo: Path) -> list[Path]:
    files: list[Path] = []
    for current, dirs, names in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in IGNORE_DIRS and not d.startswith(".cache"))
        for name in names:
            path = Path(current) / name
            if path.suffix.lower() in SOURCE_EXTS or name in MANIFESTS:
                files.append(path)
    return sorted(p for p in files if archive_root(repo) not in p.parents)


def detect_stack(files: list[Path]) -> list[str]:
    names = {f.name for f in files}
    suffixes = {f.suffix.lower() for f in files}
    stacks: list[str] = []
    if names & {"pom.xml", "build.gradle", "build.gradle.kts"} or suffixes & {".java", ".kt"}:
        stacks.append("Java/Kotlin")
    if "package.json" in names or suffixes & {".ts", ".tsx", ".vue", ".js", ".jsx"}:
        stacks.append("TypeScript/JavaScript")
    if "Cargo.toml" in names or ".rs" in suffixes:
        stacks.append("Rust")
    if "go.mod" in names or ".go" in suffixes:
        stacks.append("Go")
    if names & {"pyproject.toml", "requirements.txt"} or ".py" in suffixes:
        stacks.append("Python")
    if names & {"CMakeLists.txt", "Makefile", "meson.build"} or suffixes & {".c", ".h", ".cpp"}:
        stacks.append("C/C++")
    return stacks or ["待识别"]


def classify_system(name: str, files: list[Path]) -> str:
    lowered = name.lower()
    if lowered in FRONTEND_HINTS or any(p.suffix.lower() == ".vue" for p in files):
        return "前端"
    if lowered in BACKEND_HINTS or any(p.suffix.lower() in {".java", ".kt", ".go"} for p in files):
        return "后端"
    return name if name not in {".", "root"} else "主工程"


def discover_system_roots(repo: Path) -> list[tuple[str, Path]]:
    """保守识别顶层子系统；复杂仓库由 Agent 根据源码修正名称和边界。"""
    children: list[tuple[str, Path]] = []
    for child in sorted(repo.iterdir()):
        if not child.is_dir() or child.name in IGNORE_DIRS or child.name.startswith("."):
            continue
        files = walk_source_files(child, repo)
        if not files:
            continue
        near_manifest = any(p.parent == child and p.name in MANIFESTS for p in files)
        explicit_name = child.name.lower() in FRONTEND_HINTS | BACKEND_HINTS
        if near_manifest or explicit_name:
            children.append((classify_system(child.name, files), child))
    if len(children) >= 2 or any(name in {"前端", "后端"} for name, _ in children):
        return children
    return [("主工程", repo)]


def source_relative_parts(path: Path, system_root: Path) -> list[str]:
    parts = list(path.relative_to(system_root).parts[:-1])
    joined = "/".join(parts)
    markers = ["src/main/java/", "src/main/kotlin/", "src/", "lib/", "app/"]
    for marker in markers:
        if marker in joined + "/":
            tail = (joined + "/").split(marker, 1)[1].strip("/")
            return [p for p in tail.split("/") if p]
    return parts


def guess_module(path: Path, system_root: Path) -> str:
    if path.name in MANIFESTS:
        return "工程配置"
    dirs = source_relative_parts(path, system_root)
    lowered = [p.lower() for p in dirs]
    for i, part in enumerate(lowered):
        if part in LAYER_DIRS:
            if i + 1 < len(dirs):
                return dirs[i + 1]
            stem = re.sub(r"(?:controller|service|repository|api|view|page)$", "", path.stem, flags=re.I)
            return stem or part
    # Java 包名前缀通常较深，末级目录比公司域名更接近业务模块。
    if "src/main/java/" in path.as_posix() or "src/main/kotlin/" in path.as_posix():
        return dirs[-1] if dirs else "核心"
    if dirs:
        return dirs[0]
    return "核心"


def extract_symbols(path: Path) -> list[str]:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return []
    patterns = [
        r"\b(?:class|interface|enum|record|struct|trait)\s+([A-Za-z_][A-Za-z0-9_]*)",
        r"\b(?:function|def|fn)\s+([A-Za-z_][A-Za-z0-9_]*)",
        r"\b(?:export\s+)?(?:const|let|var)\s+([A-Za-z_][A-Za-z0-9_]*)",
        r"^\s*(?:public\s+|private\s+|protected\s+)?[A-Za-z_][\w<>, ?\[\]]*\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(",
    ]
    found: list[str] = []
    for pattern in patterns:
        found.extend(m.group(1) for m in re.finditer(pattern, text, flags=re.MULTILINE))
    return list(dict.fromkeys(found))[:20]


def extract_routes(path: Path) -> list[str]:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return []
    patterns = [
        r"@(?:RequestMapping|GetMapping|PostMapping|PutMapping|DeleteMapping|PatchMapping)\s*\(\s*(?:value\s*=\s*)?[\"']([^\"']+)",
        r"\b(?:router|app)\.(?:get|post|put|delete|patch)\s*\(\s*[\"']([^\"']+)",
        r"\b(?:client|http|axios)\.(?:get|post|put|delete|patch)\s*\(\s*[\"']([^\"']+)",
        r"\bpath\s*:\s*[\"']([^\"']+)[\"']",
        r"\b(?:url|endpoint)\s*:\s*[\"']([^\"']+)[\"']",
    ]
    routes: list[str] = []
    for pattern in patterns:
        routes.extend(m.group(1) for m in re.finditer(pattern, text, flags=re.MULTILINE))
    bases = re.findall(r"@RequestMapping\s*\(\s*(?:value\s*=\s*)?[\"']([^\"']+)", text)
    methods = re.findall(r"@(?:GetMapping|PostMapping|PutMapping|DeleteMapping|PatchMapping)\s*\(\s*(?:value\s*=\s*)?[\"']([^\"']+)", text)
    for base in bases:
        for method in methods:
            routes.append(f"{base.rstrip('/')}/{method.lstrip('/')}")
    return list(dict.fromkeys(routes))[:20]


def scan_repo(repo: Path) -> dict:
    systems: dict[str, dict] = {}
    total = 0
    used_slugs: Counter[str] = Counter()
    for display_name, root in discover_system_roots(repo):
        files = walk_source_files(root, repo)
        total += len(files)
        base_slug = slugify(root.name if root != repo else "main")
        used_slugs[base_slug] += 1
        system_slug = base_slug if used_slugs[base_slug] == 1 else f"{base_slug}-{used_slugs[base_slug]}"
        modules: dict[str, list[dict]] = defaultdict(list)
        for path in files:
            module = guess_module(path, root)
            modules[module].append({
                "path": rel(path, repo),
                "symbols": extract_symbols(path),
                "routes": extract_routes(path),
            })
        systems[system_slug] = {
            "name": display_name,
            "root": "." if root == repo else rel(root, repo),
            "stacks": detect_stack(files),
            "file_count": len(files),
            "modules": dict(sorted(modules.items())),
        }
    return {
        "schema_version": SCHEMA_VERSION,
        "repo": str(repo),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "file_count": total,
        "systems": systems,
    }


def module_doc_path(system_slug: str, module_name: str) -> str:
    return f"systems/{system_slug}/modules/{slugify(module_name)}.md"


def root_index(scan: dict, features: list[Path], decisions: list[Path]) -> str:
    rows = []
    for slug, system in scan["systems"].items():
        keywords = "、".join([system["name"], system["root"], *system["stacks"]])
        rows.append(f"| {system['name']} | `{system['root']}` | {keywords} | [进入总览](systems/{slug}/overview.md) |")
    feature_lines = [f"- [{p.name}](features/{p.name}/request.md)" for p in sorted(features)] or ["- 暂无"]
    decision_lines = [f"- [{p.stem}](decisions/{p.name})" for p in sorted(decisions)] or ["- 暂无"]
    return f"""# 项目知识库总览

> 这是人和 Agent 的共同入口。回答问题时先在本页判断子系统，再进入子系统总览，最后读取目标模块文档；不要跳过层级直接全库搜索。

## 项目摘要

- 仓库用途：待结合 README、入口与业务代码补全
- 子系统数量：{len(scan['systems'])}
- 已盘点源码与构建文件：{scan['file_count']}
- 最近机械扫描：{scan['generated_at']}

## 子系统导航

| 子系统 | 代码范围 | 识别词 | 下一步 |
| --- | --- | --- | --- |
{chr(10).join(rows)}

## 跨系统主链路

待补充用户请求、前端调用、后端处理、持久化或外部依赖之间的端到端链路，并链接对应模块。

## 全局约束

待补充认证、权限、错误码、日志、事务、生成代码、兼容性等跨系统规则。

## 需求历史

{chr(10).join(feature_lines)}

## 长期决策

{chr(10).join(decision_lines)}

## 无法定位时

先查看 [仓库机械地图](inventory/repo-map.md)。只有总览缺失路由时才做关键词检索，并在查清后补回本页或对应子系统总览。
"""


def system_overview(system_slug: str, system: dict) -> str:
    rows = []
    for module, entries in system["modules"].items():
        route_terms = list(dict.fromkeys(r for item in entries for r in item["routes"]))[:4]
        symbol_terms = list(dict.fromkeys(s for item in entries for s in item["symbols"]))[:5]
        clues = "、".join(route_terms + symbol_terms) or "待源码核对"
        rows.append(f"| {module} | 待补充一句话职责 | {clues} | [模块文档](modules/{slugify(module)}.md) |")
    return f"""# {system['name']}子系统总览

> 本页负责把问题路由到模块，不承载模块实现细节。阅读本页后，只打开命中的模块文档和它链接的源码。

## 边界与职责

- 代码范围：`{system['root']}`
- 技术栈：{', '.join(system['stacks'])}
- 负责：待核对
- 不负责：待核对

## 模块导航

| 模块 | 职责摘要 | 接口、路由与检索词 | 下一步 |
| --- | --- | --- | --- |
{chr(10).join(rows)}

## 子系统入口与主链路

待补充启动入口、请求入口、核心编排路径及关键依赖，并链接到模块文档。

## 共享约束

待补充本子系统的认证、异常、事务、缓存、日志、状态管理、构建与测试约定。

## 模块边界待确认

机械分组只是候选。Agent 必须根据业务职责合并按技术层拆散的文件，并拆开职责不同的大目录。
"""


def module_template(system: dict, module: str, entries: list[dict]) -> str:
    files = "\n".join(f"- `{item['path']}`" for item in entries[:40]) or "- 待补充"
    found_routes = list(dict.fromkeys(r for item in entries for r in item["routes"]))
    route_rows = "\n".join(f"| `{route}` | 待补充 | 待补充 | 待补充 |" for route in found_routes) or "| 待补充 | 待补充 | 待补充 | 待补充 |"
    return f"""# {module}模块

> 所属子系统：{system['name']}。本文既是人的维护手册，也是 Agent 定位实现的证据索引；结论须用仓库相对路径锚定。

## 一句话说明

待阅读源码后，用非框架术语说明该模块解决什么业务问题。

## 职责边界

- 负责：待补充
- 不负责：待补充
- 上游调用者：待补充
- 下游依赖：待补充

## 接口目录

| 方法与路径 / 调用入口 | 用途 | 入口实现 | 核心实现 |
| --- | --- | --- | --- |
{route_rows}

每个接口都应填写方法、完整路径、Controller/Handler/函数、核心 Service/UseCase，并在下节解释实现，不得只抄注解或函数签名。

## 接口与实现详解

### `<METHOD> <path>` 或 `<公开函数>`

- 用途与调用方：待补充
- 鉴权与前置条件：待补充
- 请求参数：待补充必填项、默认值、校验和示例
- 返回结果：待补充成功结构、分页或状态变化
- 实现链路：`入口` → `业务编排` → `数据访问/外部服务`
- 关键分支：待补充过滤、权限、事务、缓存、幂等或降级逻辑
- 异常与错误码：待补充
- 代码证据：待补充到具体文件和符号
- 测试证据：待补充

若有多个接口，为每个接口复制一个三级标题；接口很多时按业务动作分组，但仍保留逐接口定位信息。

## 核心实现与数据流

用编号步骤解释正常路径和关键分支，使不了解代码的人能顺着路径理解；必要时补 Mermaid 图。待补充。

## 数据与状态

待补充核心模型、字段语义、表/索引、状态机、缓存键、事件或前端状态归属。

## 配置、权限与外部依赖

待补充配置项、权限规则、第三方服务、跨模块契约及失效行为。

## 修改指南

- 常见扩展点：待补充
- 修改时必须同步的位置：待补充
- 容易踩坑的隐含约束：待补充

## 构建、测试与排障

- 最小验证命令：待补充
- 关键测试：待补充
- 常见故障定位：待补充症状、日志/指标、排查入口

## 关键文件

{files}

## 关联知识

- 相关需求：待补充链接
- 相关决策：待补充链接
- 相邻模块：待补充链接

## 待确认项

- 待补充；完成初始化前必须明确哪些是真未知，不能用笼统“待补充”代替调查。
"""


def render_repo_map(scan: dict) -> str:
    lines = ["# 仓库机械地图", "", f"- 生成时间：{scan['generated_at']}", f"- 文件数：{scan['file_count']}", ""]
    for slug, system in scan["systems"].items():
        lines.extend([f"## {system['name']}（`{system['root']}`）", ""])
        for module, entries in system["modules"].items():
            lines.extend([f"### {module}", ""])
            for item in entries[:80]:
                extras = [*item["routes"][:4], *item["symbols"][:6]]
                suffix = f" — {', '.join(extras)}" if extras else ""
                lines.append(f"- `{item['path']}`{suffix}")
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def feature_templates(title: str) -> dict[str, str]:
    common = f"- 日期：{today()}\n- 状态：草稿\n"
    return {
        "request.md": f"# {title} - 需求\n\n{common}\n## 用户需求\n\n待补充。\n\n## 目标与范围\n\n待补充。\n\n## 非目标与约束\n\n待补充。\n\n## 待确认问题\n\n待补充。\n",
        "spec.md": f"# {title} - 规格\n\n## 预期行为\n\n待补充。\n\n## 受影响子系统与模块\n\n待补充链接。\n\n## 输入、输出与异常\n\n待补充。\n\n## 验收条件\n\n待补充。\n",
        "implementation.md": f"# {title} - 实现\n\n## 实现摘要与调用链\n\n待补充。\n\n## 变更文件与取舍\n\n待补充。\n\n## 配置、数据与兼容性\n\n待补充。\n",
        "verification.md": f"# {title} - 验证\n\n## 自动化与手动检查\n\n待补充。\n\n## 结果、测试数据与缺口\n\n待补充。\n",
    }


def refresh_generated(repo: Path, scan: dict) -> None:
    arc = archive_root(repo)
    write_text(arc / "inventory" / "repo-map.md", render_repo_map(scan))
    write_text(arc / "inventory" / "navigation.json", json.dumps(scan, indent=2, ensure_ascii=False))
    for system_slug, system in scan["systems"].items():
        write_if_missing(arc / "systems" / system_slug / "overview.md", system_overview(system_slug, system))
        for module, entries in system["modules"].items():
            write_if_missing(arc / module_doc_path(system_slug, module), module_template(system, module, entries))
    features = [p for p in (arc / "features").glob("*") if p.is_dir()]
    decisions = list((arc / "decisions").glob("*.md"))
    # 总览包含人工维护的职责与路由，机械刷新绝不能覆盖它。
    write_if_missing(arc / "INDEX.md", root_index(scan, features, decisions))
    write_text(arc / "inventory" / "schema-version", f"{SCHEMA_VERSION}\n")


def ensure_archive(repo: Path) -> None:
    if not archive_root(repo).exists():
        raise SystemExit("未找到知识库，请先执行 init。")


def command_init(args: argparse.Namespace) -> None:
    repo = repo_root(args.repo)
    arc = archive_root(repo)
    for child in ["inventory", "systems", "features", "decisions", "inbox"]:
        (arc / child).mkdir(parents=True, exist_ok=True)
    scan = scan_repo(repo)
    refresh_generated(repo, scan)
    print(f"已在 {arc} 初始化 v{SCHEMA_VERSION} 分层知识库；骨架仍需 Agent 核对源码并补全。")


def command_scan(args: argparse.Namespace) -> None:
    repo = repo_root(args.repo)
    ensure_archive(repo)
    scan = scan_repo(repo)
    if args.update:
        refresh_generated(repo, scan)
        print("已更新机械地图并补建缺失的导航与模块文档；未覆盖人工内容。")
    else:
        print(render_repo_map(scan))


def command_new_feature(args: argparse.Namespace) -> None:
    repo = repo_root(args.repo)
    ensure_archive(repo)
    feature_dir = archive_root(repo) / "features" / f"{today()}-{slugify(args.title)}"
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
    addition = f"\n\n## 归档记录 {datetime.now().isoformat(timespec='seconds')}\n\n{args.summary}\n\n### 变更文件\n\n{touched}\n"
    write_text(impl, existing.rstrip() + addition)
    command_scan(argparse.Namespace(repo=str(repo), update=True))


def git_changed_files(repo: Path, since: str | None) -> list[str]:
    if since:
        code, out = run_git(repo, ["diff", "--name-only", since, "--"])
        return [] if code else [line for line in out.splitlines() if line and not line.startswith(".repo-knowledge/")]
    code, out = run_git(repo, ["status", "--short"])
    if code:
        return []
    files = []
    for line in out.splitlines():
        payload = line[3:].split(" -> ")[-1].strip()
        if payload and not payload.startswith(".repo-knowledge/"):
            files.append(payload)
    return files


def command_sync(args: argparse.Namespace) -> None:
    repo = repo_root(args.repo)
    ensure_archive(repo)
    files = git_changed_files(repo, args.since)
    lines = [
        f"# 同步记录 {now_stamp()}", "", f"- 比较基线：{args.since or '工作区与暂存区改动'}",
        f"- 变更文件数：{len(files)}", "", "## 变更文件", "",
        *(f"- `{f}`" for f in files), "", "## 分层更新清单", "",
        "- [ ] 从根总览判断受影响子系统。", "- [ ] 更新子系统总览中的模块路由与检索词。",
        "- [ ] 更新每个受影响模块的接口目录、实现链路、测试和风险。",
        "- [ ] 将需求意图和长期决策分别归档。", "- [ ] 运行 doctor 并记录处理结果。",
    ]
    path = archive_root(repo) / "inbox" / f"sync-{now_stamp()}.md"
    write_text(path, "\n".join(lines) + "\n")
    command_scan(argparse.Namespace(repo=str(repo), update=True))
    print(f"已生成同步记录 {path}")


def query_terms(query: str) -> list[str]:
    chunks = re.findall(r"[\u4e00-\u9fff]+|[A-Za-z][A-Za-z0-9_.-]*|\d+", query.lower())
    terms: list[str] = []
    for chunk in chunks:
        terms.append(chunk)
        if re.fullmatch(r"[\u4e00-\u9fff]+", chunk) and len(chunk) > 2:
            terms.extend(chunk[i:i + 2] for i in range(len(chunk) - 1))
        if "/" in chunk:
            terms.extend(p for p in chunk.split("/") if p)
    return list(dict.fromkeys(t for t in terms if t))


def text_score(path: Path, terms: list[str]) -> int:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
    except OSError:
        return 0
    return sum((4 if term in path.as_posix().lower() else 0) + min(text.count(term), 8) for term in terms)


def command_context(args: argparse.Namespace) -> None:
    repo = repo_root(args.repo)
    ensure_archive(repo)
    arc = archive_root(repo)
    terms = query_terms(args.query)
    index = arc / "INDEX.md"
    print(f"1\t根总览\t{rel(index, repo)}\t先判断前端、后端或其他子系统")
    overviews = list((arc / "systems").glob("*/overview.md"))
    ranked_systems = sorted(((text_score(p, terms), p) for p in overviews), key=lambda x: (-x[0], x[1].as_posix()))
    selected = [ranked_systems[0][1]] if ranked_systems else []
    for overview in selected:
        print(f"2\t子系统总览\t{rel(overview, repo)}\t从模块导航匹配职责、接口、路由或检索词")
        modules = list((overview.parent / "modules").glob("*.md"))
        ranked_modules = sorted(((text_score(p, terms), p) for p in modules), key=lambda x: (-x[0], x[1].as_posix()))
        for score, module in ([x for x in ranked_modules if x[0] > 0][: args.limit] or ranked_modules[:1]):
            print(f"3\t模块文档\t{rel(module, repo)}\t匹配分 {score}；读取接口实现链路和证据路径")
    print("4\t源码核验\t读取模块文档链接的最少源码与测试\t文档用于路由，最终事实以代码和测试为准")


def command_doctor(args: argparse.Namespace) -> None:
    repo = repo_root(args.repo)
    ensure_archive(repo)
    arc = archive_root(repo)
    errors: list[str] = []
    warnings: list[str] = []
    if not (arc / "INDEX.md").exists():
        errors.append("缺少 INDEX.md")
    overviews = list((arc / "systems").glob("*/overview.md"))
    if not overviews:
        errors.append("缺少 systems/<子系统>/overview.md")
    module_docs = list((arc / "systems").glob("*/modules/*.md"))
    if not module_docs:
        errors.append("缺少模块独立文档")
    required_sections = ["## 接口目录", "## 接口与实现详解", "## 核心实现与数据流", "## 构建、测试与排障"]
    for path in module_docs:
        text = path.read_text(encoding="utf-8", errors="ignore")
        for section in required_sections:
            if section not in text:
                errors.append(f"{rel(path, repo)} 缺少章节：{section}")
        placeholders = text.count("待补充")
        if placeholders:
            warnings.append(f"{rel(path, repo)} 仍有 {placeholders} 处待补充")
        if not re.search(r"`[^`]+[/\\][^`]+`", text):
            warnings.append(f"{rel(path, repo)} 缺少源码路径证据")
    for path in [arc / "INDEX.md", *overviews, *module_docs]:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for target in re.findall(r"\[[^]]+\]\(([^)#]+)(?:#[^)]+)?\)", text):
            if "://" not in target and not (path.parent / target).resolve().exists():
                errors.append(f"{rel(path, repo)} 包含坏链：{target}")
    print(f"错误 {len(errors)}，警告 {len(warnings)}")
    for item in errors:
        print(f"ERROR\t{item}")
    for item in warnings:
        print(f"WARN\t{item}")
    if errors or (args.strict and warnings):
        raise SystemExit(1)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init"); init.add_argument("--repo", required=True); init.set_defaults(func=command_init)
    scan = sub.add_parser("scan"); scan.add_argument("--repo", required=True); scan.add_argument("--update", action="store_true"); scan.set_defaults(func=command_scan)
    feature = sub.add_parser("new-feature"); feature.add_argument("--repo", required=True); feature.add_argument("--title", required=True); feature.set_defaults(func=command_new_feature)
    archive = sub.add_parser("archive"); archive.add_argument("--repo", required=True); archive.add_argument("--feature", required=True); archive.add_argument("--summary", required=True); archive.add_argument("--files", default=""); archive.set_defaults(func=command_archive)
    sync = sub.add_parser("sync"); sync.add_argument("--repo", required=True); sync.add_argument("--since"); sync.set_defaults(func=command_sync)
    context = sub.add_parser("context"); context.add_argument("--repo", required=True); context.add_argument("--query", required=True); context.add_argument("--limit", type=int, default=3); context.set_defaults(func=command_context)
    doctor = sub.add_parser("doctor"); doctor.add_argument("--repo", required=True); doctor.add_argument("--strict", action="store_true"); doctor.set_defaults(func=command_doctor)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
