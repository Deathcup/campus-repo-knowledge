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

SCHEMA_VERSION = 5
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
TECHNICAL_SUFFIXES = (
    "controller", "serviceimpl", "service", "repository", "mapper", "dao",
    "entity", "model", "api", "view", "page", "component", "store",
    "handler", "route", "test", "tests",
)


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


def system_kind(name: str, files: list[Path]) -> str:
    lowered = name.lower()
    suffixes = {p.suffix.lower() for p in files}
    if lowered in FRONTEND_HINTS or suffixes & {".vue", ".tsx", ".jsx"}:
        return "frontend"
    if lowered in BACKEND_HINTS or suffixes & {".java", ".kt", ".go", ".rs", ".cs"}:
        return "backend"
    return "general"


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
    markers = [
        "src/main/java/", "src/main/kotlin/", "src/test/java/", "src/test/kotlin/",
        "src/", "tests/", "test/", "lib/", "app/",
    ]
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
            for candidate in dirs[i + 1:]:
                if candidate.lower() not in LAYER_DIRS | {"impl", "implementation"}:
                    return candidate
            stem = path.stem
            previous = None
            while previous != stem:
                previous = stem
                stem = re.sub(
                    rf"(?:{'|'.join(TECHNICAL_SUFFIXES)})$",
                    "",
                    stem,
                    flags=re.I,
                )
            return stem or part
    # Java 包名前缀通常较深，末级目录比公司域名更接近业务模块。
    if any(marker in path.as_posix() for marker in ("src/main/java/", "src/main/kotlin/", "src/test/java/", "src/test/kotlin/")):
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


def extract_endpoints(path: Path) -> list[str]:
    """提取带方法的后端/客户端端点，用于区分同一路径上的不同接口。"""
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return []
    endpoints: list[str] = []
    spring_methods = {
        "GetMapping": "GET",
        "PostMapping": "POST",
        "PutMapping": "PUT",
        "DeleteMapping": "DELETE",
        "PatchMapping": "PATCH",
    }
    bases = re.findall(
        r"@RequestMapping\s*\(\s*(?:value\s*=\s*)?[\"']([^\"']+)",
        text,
    )
    base = bases[0] if bases else ""
    for annotation, raw_path in re.findall(
        r"@(GetMapping|PostMapping|PutMapping|DeleteMapping|PatchMapping)"
        r"(?:\s*\(\s*(?:value\s*=\s*)?[\"']([^\"']*)[\"'][^)]*\))?",
        text,
    ):
        combined = f"{base.rstrip('/')}/{raw_path.lstrip('/')}" if base else (raw_path or "/")
        endpoints.append(f"{spring_methods[annotation]} {combined or '/'}")
    for method, raw_path in re.findall(
        r"\b(?:router|app|client|http|axios)\.(get|post|put|delete|patch)"
        r"\s*\(\s*[\"']([^\"']+)",
        text,
        flags=re.I,
    ):
        endpoints.append(f"{method.upper()} {raw_path}")
    return list(dict.fromkeys(endpoints))[:30]


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
            if path.name in MANIFESTS:
                continue
            module = guess_module(path, root)
            modules[module].append({
                "path": rel(path, repo),
                "symbols": extract_symbols(path),
                "routes": extract_routes(path),
                "endpoints": extract_endpoints(path),
            })
        systems[system_slug] = {
            "name": display_name,
            "kind": system_kind(root.name if root != repo else display_name, files),
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


def default_module_map(scan: dict) -> dict:
    return {
        "_instructions": (
            "把机械候选名映射为稳定业务模块名；Controller/Service/Mapper、同一业务实体和相邻用例"
            "应映射到同一名称。scan --update 会按映射合并源码并生成导航。"
        ),
        "systems": {
            system_slug: {module: module for module in system["modules"]}
            for system_slug, system in scan["systems"].items()
        },
    }


def apply_module_map(scan: dict, arc: Path) -> dict:
    path = arc / "inventory" / "module-map.json"
    try:
        configured = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        configured = {"systems": {}}
    for system_slug, system in scan["systems"].items():
        mappings = configured.get("systems", {}).get(system_slug, {})
        merged: dict[str, list[dict]] = defaultdict(list)
        for candidate, entries in system["modules"].items():
            target = mappings.get(candidate, candidate)
            if not isinstance(target, str) or not target.strip():
                target = candidate
            merged[target.strip()].extend(entries)
        system["modules"] = dict(sorted(merged.items()))
    return scan


def module_doc_path(system_slug: str, module_name: str) -> str:
    return f"systems/{system_slug}/modules/{slugify(module_name)}/overview.md"


def module_dir_path(system_slug: str, module_name: str) -> str:
    return f"systems/{system_slug}/modules/{slugify(module_name)}"


def leaf_routes(entries: list[dict]) -> list[str]:
    """保留最具体的路由，避免同时为 `/x`、`/query`、`/x/query` 建三份文档。"""
    routes = list(dict.fromkeys(r for item in entries for r in item["routes"]))
    absolute = [route for route in routes if route.startswith("/")]
    leaves = [
        route for route in absolute
        if not any(
            other != route and other.startswith(route.rstrip("/") + "/")
            for other in absolute
        )
    ]
    return leaves or routes


def backend_entrypoints(entries: list[dict]) -> list[str]:
    endpoints = list(dict.fromkeys(
        endpoint
        for item in entries
        for endpoint in item.get("endpoints", [])
    ))
    return endpoints or leaf_routes(entries)


def topic_filename(prefix: str, value: str, used: set[str]) -> str:
    base = slugify(value).strip("-") or "root"
    candidate = f"{prefix}-{base}.md"
    index = 2
    while candidate in used:
        candidate = f"{prefix}-{base}-{index}.md"
        index += 1
    used.add(candidate)
    return candidate


def backend_interface_template(module: str, route: str, entries: list[dict]) -> str:
    evidence = "\n".join(
        f"- `{item['path']}`：检查 `{route}` 的入口、调用链和测试。"
        for item in entries
        if route in item.get("endpoints", []) or route in item["routes"]
    ) or "\n".join(f"- `{item['path']}`" for item in entries[:8])
    return f"""# {module}：`{route}` 实现详解

> 本文只负责这一个接口或入口的真实实现。读完应能解释它为何存在、每一步怎样执行、失败时留下什么结果，以及修改它需要同步哪些代码与测试。

## 业务场景与调用方

说明谁在什么业务流程中调用 `{route}`、调用前必须具备的状态，以及成功和失败分别对调用方意味着什么。

## 请求、响应与业务语义

| 字段/载体 | 来源与类型 | 业务含义 | 默认值/单位/时区/枚举 | 校验与字段联动 | 进入哪一步 |
| --- | --- | --- | --- | --- | --- |
| 逐字段填写 | path/query/header/body/file | 不复制类型，要解释业务语义 | 写清缺省与兼容规则 | 写清跨字段条件 | 链接实现步骤 |

响应也逐字段说明业务结果、错误语义和调用方如何消费。没有请求体、响应体或某类字段时，在表中写“无”并给入口证据，不能省略本节。

## 鉴权、数据范围与前置校验

说明认证入口、角色/租户/组织/所有权限制、参数规范化和校验顺序；指出失败发生在调用链哪一步。

## 完整实现链路

用 5–12 个编号步骤从 Controller/Handler 追到业务服务、领域规则、数据访问或外部系统。每一步写清“输入状态 → 判断/转换/查询 → 输出状态 → 代码符号”。

## 关键业务逻辑与算法

解释条件构造、计算、聚合、匹配、排序、分页、映射或状态转换。给出必要伪代码和关键分支原因，不粘贴大段源码。

## 数据读写与副作用

列出读取和写入的表、索引、缓存、事件、文件或第三方服务；说明顺序、字段变化和用户可见结果。

## 事务、并发、幂等与失败恢复

说明事务边界、锁/版本/幂等键、重试或补偿。若当前没有保护，说明证据、可能竞态和开发影响。

## 异常、错误码与可观测性

按触发条件列出异常转换、HTTP/业务错误、日志、指标、trace 和审计点，并说明敏感信息约束。

## 测试与修改指南

列出覆盖正常、权限、边界、并发和依赖失败的测试；说明增加相邻参数、规则或副作用时要修改的具体文件类别和契约。

## 源码与测试证据

{evidence}
"""


def frontend_page_template(module: str, page_path: str, entries: list[dict]) -> str:
    page_name = Path(page_path).stem
    return f"""# {module}：{page_name} 页面实现详解

> 本文负责 `{page_path}` 对应页面或 View 的完整实现。读完应能从用户动作追踪到组件、状态、接口和反馈，并能安全增加相邻功能。

## 页面业务目标与用户

说明页面服务的角色、解决的业务问题、进入前置条件，以及它与列表、详情、编辑或其他页面的衔接。

## 路由、入口与离开行为

说明菜单/父页面入口、路由参数、守卫、权限、重定向、直接访问、返回和卸载清理。

## View 编排与重要组件树

画出根 View 到重要业务组件的树，并填写职责表：

| View/组件 | 用户能力 | 父子契约 | 状态所有者 | API/路由/弹窗副作用 | 代码证据 |
| --- | --- | --- | --- | --- | --- |
| 逐个重要组件填写 | 用户能完成什么 | props/emits/slots/context | local/store/composable | 触发与反馈 | `文件#符号` |

## 首屏初始化流程

用编号步骤说明参数读取、默认状态、并行/串行请求、响应转换、首屏渲染，以及加载、空数据、无权限和请求失败。

## 用户操作与功能点

按筛选、分页、查看、编辑、提交、删除、导出等真实动作分别追踪：控件 → 处理函数 → 校验 → 状态 → API → 成功/失败反馈。

## 状态、计算属性与生命周期

说明 local/store/composable/query 状态的所有者、更新者、消费者、缓存/失效、watch/effect、竞态、取消、防抖和卸载清理。

## API 协作与数据转换

| 用户动作/初始化 | API | 请求组装 | 响应转换与状态落点 | 失败反馈 | 后端实现 |
| --- | --- | --- | --- | --- | --- |
| 逐接口填写 | 方法与路径 | 默认值、枚举、时间、分页 | DTO→ViewModel/store | 保留/回滚/重试 | 同仓时链接接口文档 |

没有 API 的静态页面也要在表中写明“当前无 API”，并链接证明页面没有请求的源码。

## 展示规则与边界场景

列出显示/隐藏、启用/禁用、可编辑、字段联动、排序格式化、重复提交、乐观更新/回滚和兼容行为的触发条件。

## 测试与修改指南

列出组件、store、API mock 和 E2E 覆盖；以增加一个相邻操作或字段为例，说明要修改的 View、组件、状态、类型、接口和测试。

## 源码与测试证据

- `{page_path}`：根 View 或页面入口。
{chr(10).join(f"- `{item['path']}`" for item in entries[:12] if item['path'] != page_path)}
"""


def detail_topic_specs(system: dict, module: str, entries: list[dict]) -> list[tuple[str, str, str]]:
    """返回 (文件名, 导航说明, 骨架内容)，确保模块必有可渐进加载的实现层。"""
    kind = system.get("kind", "general")
    used: set[str] = set()
    topics: list[tuple[str, str, str]] = []
    if kind == "backend":
        topics.append((
            "business-rules.md",
            "业务用例、规则、状态机和跨接口共性",
            backend_interface_template(module, "跨接口业务规则", entries),
        ))
        for route in backend_entrypoints(entries):
            filename = topic_filename("interface", route, used)
            topics.append((filename, f"`{route}` 的逐步实现、数据与失败路径", backend_interface_template(module, route, entries)))
        if len(topics) == 1:
            topics.append((
                "use-cases.md",
                "非 HTTP 用例、任务、消费者或公开函数的实现",
                backend_interface_template(module, "核心业务用例", entries),
            ))
    elif kind == "frontend":
        page_entries = [
            item for item in entries
            if Path(item["path"]).suffix.lower() in {".vue", ".tsx", ".jsx"}
            or any(part in {"view", "views", "page", "pages"} for part in Path(item["path"]).parts)
        ]
        for item in page_entries:
            filename = topic_filename("page", Path(item["path"]).stem, used)
            topics.append((
                filename,
                f"`{item['path']}` 页面流程、组件、状态和 API 实现",
                frontend_page_template(module, item["path"], entries),
            ))
        if not topics:
            topics.append((
                "page-main.md",
                "模块主页面或入口功能的完整前端实现",
                frontend_page_template(module, entries[0]["path"] if entries else "主页面", entries),
            ))
        topics.append((
            "components-and-state.md",
            "跨页面组件契约、共享状态、composable/store 与 API 协作",
            frontend_page_template(module, "共享组件与状态", entries),
        ))
    else:
        topics.append((
            "capabilities.md",
            "公开能力、调用链、数据和边界的详细实现",
            backend_interface_template(module, "核心能力", entries),
        ))
    topics.append((
        "development.md",
        "新增功能、兼容性、测试、运行和排障",
        backend_interface_template(module, "开发与验证", entries)
        if kind != "frontend" else frontend_page_template(module, "开发与验证", entries),
    ))
    return topics


def detail_navigation(topics: list[tuple[str, str, str]]) -> str:
    rows = "\n".join(f"| [{name}]({name}) | {purpose} |" for name, purpose, _ in topics)
    return f"""## 实现细节导航

> 先按问题选择下表中的最小文档，不要为了查询一个接口或页面加载整个模块。每个页面、接口或核心功能点都必须拥有自己的实现文档。

| 文档 | 何时读取 |
| --- | --- |
{rows}
"""


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

待补充 3–8 条最重要的业务旅程：用户目标 → 前端页面/调用方 → 后端用例 → 数据或外部系统 → 用户可见结果。每一步链接对应子系统或模块。

## 新人上手路径

待补充按业务价值排序的阅读路线，以及本地启动一条最小端到端流程的方法。

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
        rows.append(f"| {module} | 待补充一句话职责 | {clues} | [模块入口](modules/{slugify(module)}/overview.md) |")
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

待补充启动入口、主要用户/业务流程、模块协作顺序及关键依赖，并链接到模块文档。不能只列路由或包结构。

## 模块关系与典型业务旅程

用文字或 Mermaid 图解释模块如何协作。前端说明页面、状态、组件与 API 的关系；后端说明入口、业务用例、数据与外部依赖的关系。

## 新人开发入口

说明首次开发通常从哪些模块开始，如何启动、准备数据、验证一条最小业务流程，以及哪些共享规则必须先读。

## 共享约束

待补充本子系统的认证、异常、事务、缓存、日志、状态管理、构建与测试约定。

## 模块边界待确认

机械分组只是候选。Agent 必须根据业务职责合并按技术层拆散的文件，并拆开职责不同的大目录。
"""


def common_module_header(system: dict, module: str, topics: list[tuple[str, str, str]]) -> str:
    return f"""# {module}模块开发手册

> 所属子系统：{system['name']}。目标读者是只熟悉编程语言、第一次接触本服务的开发者。本文完成后，读者应能理解业务、解释主要流程、定位关键实现，并安全地开始开发。

## 阅读地图

用 5–10 行说明建议阅读顺序：先在本页理解模块边界和总体流程，再按接口、页面或功能点进入实现细节文档，最后如何运行和验证。

{detail_navigation(topics)}

## 业务背景与用户价值

说明这个模块为谁解决什么问题、在完整产品流程中处于哪一环、业务成功和失败分别意味着什么。不得只描述“提供增删改查”。

## 业务术语与核心概念

| 术语 | 面向新人的解释 | 代码中的对应物 |
| --- | --- | --- |
| 待调查 | 说明业务含义、生命周期和与相近概念的区别 | `类型/字段/文件#符号` |

## 角色、权限与职责边界

- 使用者与角色：列出谁会触发本模块以及各自能做什么。
- 权限与数据范围：说明租户、组织、角色、所有权或可见性限制在何处生效。
- 本模块负责：按业务结果描述。
- 本模块不负责：指出相邻模块并链接。
- 上下游：说明输入从哪里来、结果被谁消费。
"""


def frontend_module_template(system: dict, module: str, entries: list[dict], topics: list[tuple[str, str, str]]) -> str:
    files = "\n".join(f"- `{item['path']}`" for item in entries[:40]) or "- 待补充"
    found_routes = list(dict.fromkeys(r for item in entries for r in item["routes"]))
    route_rows = "\n".join(f"| `{route}` | 触发场景待调查 | 页面/View 待调查 | 权限/参数待调查 |" for route in found_routes) or "| 路由待调查 | 触发场景待调查 | 页面/View 待调查 | 权限/参数待调查 |"
    return common_module_header(system, module, topics) + f"""

## 页面入口、路由与访问条件

| 页面路由/入口 | 用户从哪里进入 | 根 View | 路由参数、权限与守卫 |
| --- | --- | --- | --- |
{route_rows}

说明菜单、父页面、重定向、动态路由、权限指令和直接访问 URL 时的行为。

## 页面总体流程

从用户视角完整讲述“进入页面 → 初始化 → 查看/筛选/编辑 → 提交 → 成功或失败反馈”的过程。至少覆盖首屏加载、主要成功路径、空数据、权限不足、接口失败和离开页面；使用编号步骤，复杂流程补 Mermaid 流程图。

## View 与重要组件结构

先给出组件树，再解释重要组件为什么存在。不要只复制 import 列表。

```text
<RootView>（页面编排、查询状态）
├─ <FilterPanel>（收集筛选条件、触发查询）
├─ <ResultTable>（展示结果、分页、选择）
└─ <DetailDialog>（查看详情、关闭后刷新条件）
```

| View/组件 | 用户看到什么 | 业务职责 | 关键 props/emits/slots | 状态与接口 | 代码证据 |
| --- | --- | --- | --- | --- | --- |
| 待调查 | 不描述样式，描述用户能力 | 解释为何独立、与父子组件如何协作 | 列出影响业务的契约 | local/store/query/API | `文件#符号` |

“重要组件”包括承载业务动作、状态边界、复杂展示或复用契约的组件；纯样式包装可合并说明。

## 状态、数据与副作用

| 状态/数据 | 来源 | 所有者 | 更新时机 | 消费者 | 重置/缓存/持久化 |
| --- | --- | --- | --- | --- | --- |
| 待调查 | route/store/API/props | View、store 或 composable | 触发条件 | 组件或请求 | 生命周期与失效规则 |

解释计算属性、watch/effect、异步竞态、请求取消、防抖、分页、缓存、URL 同步和组件卸载清理；没有某项时明确写“不涉及”及依据。

## 用户交互与关键前端逻辑

按业务动作分别解释：触发控件 → 事件处理函数 → 校验/转换 → 状态变化 → API 调用 → 页面反馈。覆盖禁用条件、二次确认、错误提示、乐观更新或回滚、重复提交和并发请求。

## 接口协作

| API 客户端/接口 | 由哪个动作触发 | 请求如何组装 | 响应如何转换和落入状态 | 失败时用户看到什么 |
| --- | --- | --- | --- | --- |
| 待调查 | 页面加载/按钮/分页等 | 默认值、过滤和格式转换 | DTO→ViewModel/store | 提示、保留状态、重试 |

逐个解释重要接口，不得只写路径和入参出参。链接后端模块文档（若同仓存在），指出前后端字段、枚举、分页和时间语义。

## 业务规则与边界场景

列出前端实际执行或展示的业务规则：显示/隐藏、可编辑条件、字段联动、状态转换、数据范围、格式化、排序、空态和降级。对每条规则写触发条件、行为结果和代码证据。

## 开发指南

### 增加或修改一个业务能力

按真实工程给出操作顺序：需要修改哪些 View、组件、composable/store、API 类型、路由、权限和测试；说明哪些生成文件不能手改。

### 安全修改清单

- 必须保持的组件/API 契约：待调查并替换。
- 容易漏改的联动位置：待调查并替换。
- 常见错误与原因：待调查并替换。

## 构建、测试与排障

- 本模块最小启动与验证命令：待调查并替换。
- 单元/组件/E2E 测试及各自覆盖的用户场景：待调查并替换。
- 常见症状 → 检查状态/网络/组件/路由的位置 → 关键代码入口：待调查并替换。

## 关键文件

{files}

## 关联知识

- 相关需求：待调查并替换为链接或“暂无”
- 相关决策：待调查并替换为链接或“暂无”
- 相邻模块：待调查并替换为链接

## 待确认项

- 只保留无法从仓库确认的具体问题，并附已查证据；不得保留模板提示或笼统未知。
"""


def backend_module_template(system: dict, module: str, entries: list[dict], topics: list[tuple[str, str, str]]) -> str:
    files = "\n".join(f"- `{item['path']}`" for item in entries[:40]) or "- 待调查"
    found_routes = list(dict.fromkeys(r for item in entries for r in item["routes"]))
    route_rows = "\n".join(f"| `{route}` | 业务用途待调查 | 入口待调查 | 核心用例待调查 |" for route in found_routes) or "| 接口待调查 | 业务用途待调查 | 入口待调查 | 核心用例待调查 |"
    return common_module_header(system, module, topics) + f"""

## 业务用例与总体流程

按业务用例而不是按 Controller 类组织。每个用例先用新人能理解的语言说明触发者、前置状态、成功结果和失败结果，再用 4–10 个编号步骤串起鉴权、校验、业务计算、持久化、外部调用和响应。复杂流程补 Mermaid 流程图或时序图。

## 业务规则与关键分支

| 规则/分支 | 触发条件 | 系统行为 | 为什么需要 | 代码与测试证据 |
| --- | --- | --- | --- | --- |
| 待调查 | 输入、角色或当前状态 | 返回/数据变化/副作用 | 业务约束或技术保护 | `文件#符号` |

必须覆盖权限和数据范围、状态机、重复请求、边界值、空结果、部分失败、降级和异常路径。不得用“调用 Service 处理”代替逻辑解释。

## 接口目录

| 方法与路径 / 调用入口 | 业务用途 | 入口实现 | 核心业务实现 |
| --- | --- | --- | --- |
{route_rows}

## 接口与实现详解

### `<METHOD> <path>` 或 `<事件/任务/公开函数>`

- 业务场景与调用方：待调查并替换。
- 鉴权、数据范围与前置状态：待调查并替换。
- 请求语义：解释字段的业务含义、默认值、单位、时区、校验和字段联动。
- 成功结果：说明返回值以及产生的数据、状态或事件变化。
- 完整实现链路：`入口#符号` → `业务编排#符号` → `领域规则#符号` → `数据访问/外部服务#符号`。
- 关键算法与查询：用伪代码或分步文字解释条件构造、计算、聚合、排序、分页、映射，不粘贴大段源码。
- 分支与异常：逐条说明触发条件、错误码/异常、是否产生副作用。
- 事务、并发、幂等与缓存：说明边界和失败恢复；不涉及时写依据。
- 日志、指标与审计：说明成功/失败如何观测以及敏感信息处理。
- 代码与测试证据：链接到具体文件和符号。

为每个重要接口、消费者、任务或公开入口建立独立三级标题。相似 CRUD 可以合并公共部分，但必须单列不同业务规则。

## 数据模型与持久化

| 模型/表/索引/缓存 | 业务含义 | 关键字段与约束 | 读写时机 | 生命周期与关联 |
| --- | --- | --- | --- | --- |
| 待调查 | 新人可理解的领域含义 | 主键、唯一性、状态、时间、单位 | 哪个用例读写 | 创建、变更、删除/过期 |

解释 DTO、领域模型与持久化模型之间的转换，查询条件如何落到 SQL/ES/缓存，索引或性能假设是什么。

## 事务、一致性与并发

说明事务从哪里开始和提交，跨资源一致性如何保证，锁/版本号/幂等键/去重如何工作，失败后是否重试、补偿或留下部分结果。没有显式机制时说明当前风险。

## 依赖、事件与外部副作用

| 依赖/事件 | 调用时机 | 输入输出契约 | 超时/失败/重试 | 对业务结果的影响 |
| --- | --- | --- | --- | --- |
| 待调查 | 在用例第几步 | 关键字段 | 实际策略 | 强依赖、可降级或异步最终一致 |

覆盖消息、第三方服务、文件、邮件、审计、定时任务和跨模块调用。

## 配置、权限与运行约束

解释配置键、默认值、环境差异、特性开关、权限注解/中间件、资源上限和安全约束，并给读取位置。

## 开发指南

### 增加或修改一个业务能力

按本仓库真实结构说明通常要改哪些入口、应用/领域服务、模型、仓储、迁移、事件、配置和测试；指出生成代码和兼容性要求。

### 安全修改清单

- 修改前必须确认的业务规则：待调查并替换。
- 必须同步的调用方、数据和文档：待调查并替换。
- 容易破坏的隐含约束与性能假设：待调查并替换。

## 构建、测试与排障

- 本模块最小构建、启动和测试命令：待调查并替换。
- 关键单元/集成/契约测试以及覆盖的业务分支：待调查并替换。
- 常见症状 → 日志/指标/数据检查 → 关键代码入口：待调查并替换。

## 关键文件

{files}

## 关联知识

- 相关需求：待调查并替换为链接或“暂无”
- 相关决策：待调查并替换为链接或“暂无”
- 相邻模块与调用方：待调查并替换为链接

## 待确认项

- 只保留无法从仓库确认的具体问题，并附已查证据；不得保留模板提示或笼统未知。
"""


def module_template(system: dict, module: str, entries: list[dict], topics: list[tuple[str, str, str]]) -> str:
    if system.get("kind") == "frontend":
        return frontend_module_template(system, module, entries, topics)
    return backend_module_template(system, module, entries, topics)


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
            topics = detail_topic_specs(system, module, entries)
            module_dir = arc / module_dir_path(system_slug, module)
            write_if_missing(
                arc / module_doc_path(system_slug, module),
                module_template(system, module, entries, topics),
            )
            for filename, _, content in topics:
                write_if_missing(module_dir / filename, content)
    features = [p for p in (arc / "features").glob("*") if p.is_dir()]
    decisions = list((arc / "decisions").glob("*.md"))
    # 总览包含人工维护的职责与路由，机械刷新绝不能覆盖它。
    write_if_missing(arc / "INDEX.md", root_index(scan, features, decisions))
    write_text(arc / "inventory" / "schema-version", f"{SCHEMA_VERSION}\n")


def migrate_flat_modules(repo: Path) -> tuple[int, list[str]]:
    """把 v2/v3 的 modules/<模块>.md 安全迁移到 modules/<模块>/overview.md。"""
    arc = archive_root(repo)
    moved = 0
    conflicts: list[str] = []
    for source in sorted((arc / "systems").glob("*/modules/*.md")):
        target = source.with_suffix("") / "overview.md"
        if target.exists():
            conflicts.append(
                f"{rel(source, repo)} 与 {rel(target, repo)} 同时存在，需人工合并后删除扁平文件"
            )
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        source.replace(target)
        moved += 1
    return moved, conflicts


def ensure_archive(repo: Path) -> None:
    if not archive_root(repo).exists():
        raise SystemExit("未找到知识库，请先执行 init。")


def command_init(args: argparse.Namespace) -> None:
    repo = repo_root(args.repo)
    arc = archive_root(repo)
    for child in ["inventory", "systems", "features", "decisions", "inbox"]:
        (arc / child).mkdir(parents=True, exist_ok=True)
    scan = scan_repo(repo)
    write_if_missing(
        arc / "inventory" / "module-map.json",
        json.dumps(default_module_map(scan), indent=2, ensure_ascii=False) + "\n",
    )
    scan = apply_module_map(scan, arc)
    refresh_generated(repo, scan)
    print(f"已在 {arc} 初始化 v{SCHEMA_VERSION} 分层知识库；骨架仍需 Agent 核对源码并补全。")


def command_scan(args: argparse.Namespace) -> None:
    repo = repo_root(args.repo)
    ensure_archive(repo)
    scan = scan_repo(repo)
    scan = apply_module_map(scan, archive_root(repo))
    if args.update:
        refresh_generated(repo, scan)
        print("已更新机械地图并补建缺失的导航与模块文档；未覆盖人工内容。")
    else:
        print(render_repo_map(scan))


def command_upgrade_layout(args: argparse.Namespace) -> None:
    repo = repo_root(args.repo)
    ensure_archive(repo)
    moved, conflicts = migrate_flat_modules(repo)
    for conflict in conflicts:
        print(f"CONFLICT\t{conflict}")
    if conflicts:
        raise SystemExit(1)
    print(f"已迁移 {moved} 个扁平模块文档到独立模块目录；请更新子系统总览链接并运行 doctor。")


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
        "- [ ] 更新每个受影响模块的业务流程、组件/服务协作、规则分支、接口实现、数据、开发指南和测试。",
        "- [ ] 前端复核 View、重要组件、状态、交互和 API；后端复核关键逻辑、查询/计算、事务并发和副作用。",
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
        modules = list((overview.parent / "modules").glob("*/overview.md"))
        ranked_modules = sorted(((text_score(p, terms), p) for p in modules), key=lambda x: (-x[0], x[1].as_posix()))
        for score, module in ([x for x in ranked_modules if x[0] > 0][: args.limit] or ranked_modules[:1]):
            print(f"3\t模块开发手册\t{rel(module, repo)}\t匹配分 {score}；先理解业务、流程和关键逻辑，再定位代码")
            topics = [p for p in module.parent.glob("*.md") if p.name != "overview.md"]
            ranked_topics = sorted(
                ((text_score(p, terms), p) for p in topics),
                key=lambda x: (-x[0], x[1].as_posix()),
            )
            for topic_score, topic in ([x for x in ranked_topics if x[0] > 0][: args.limit] or ranked_topics[:1]):
                print(f"4\t模块内专题\t{rel(topic, repo)}\t匹配分 {topic_score}；读取更具体的业务、实现、接口或开发细节")
    print("5\t源码核验\t读取模块手册链接的最少源码与测试\t验证文档仍与当前实现一致")


def section_body(text: str, heading: str) -> str:
    match = re.search(
        rf"(?ms)^## {re.escape(heading)}\s*$\n(.*?)(?=^## |\Z)",
        text,
    )
    return match.group(1).strip() if match else ""


def system_kinds(arc: Path) -> dict[str, str]:
    path = arc / "inventory" / "navigation.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return {slug: system.get("kind", "general") for slug, system in data.get("systems", {}).items()}


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
    flat_module_docs = list((arc / "systems").glob("*/modules/*.md"))
    if flat_module_docs:
        for path in flat_module_docs:
            errors.append(f"{rel(path, repo)} 仍是扁平模块文档，必须迁入 <模块>/overview.md")
    module_docs = list((arc / "systems").glob("*/modules/*/overview.md"))
    if not module_docs:
        errors.append("缺少模块独立文档")
    topic_docs = [
        path for path in (arc / "systems").glob("*/modules/*/*.md")
        if path.name != "overview.md"
    ]
    template_markers = [
        "待补充", "待核对", "待调查", "并替换", "KNOWLEDGE_TODO",
        "<RootView>", "<METHOD>", "<path>", "TODO", "TBD",
    ]
    for path in sorted(arc.rglob("*.md")):
        text = path.read_text(encoding="utf-8", errors="ignore")
        found = [marker for marker in template_markers if marker in text]
        if found:
            errors.append(f"{rel(path, repo)} 含禁止残留：{', '.join(found)}")
    index_path = arc / "INDEX.md"
    if index_path.exists():
        index_text = index_path.read_text(encoding="utf-8", errors="ignore")
        for section in ["项目摘要", "子系统导航", "跨系统主链路", "新人上手路径", "全局约束"]:
            body = section_body(index_text, section)
            if not body:
                errors.append(f"{rel(index_path, repo)} 缺少章节：{section}")
            elif len(re.sub(r"\s+", "", body)) < 60:
                warnings.append(f"{rel(index_path, repo)} 章节内容过浅：{section}")
        if any(marker in index_text for marker in template_markers):
            warnings.append(f"{rel(index_path, repo)} 仍有模板提示或未完成内容")
    for overview in overviews:
        overview_text = overview.read_text(encoding="utf-8", errors="ignore")
        for section in ["边界与职责", "模块导航", "子系统入口与主链路", "模块关系与典型业务旅程", "新人开发入口", "共享约束"]:
            body = section_body(overview_text, section)
            if not body:
                errors.append(f"{rel(overview, repo)} 缺少章节：{section}")
            elif len(re.sub(r"\s+", "", body)) < 60:
                warnings.append(f"{rel(overview, repo)} 章节内容过浅：{section}")
        if any(marker in overview_text for marker in template_markers):
            warnings.append(f"{rel(overview, repo)} 仍有模板提示或未完成内容")
    kinds = system_kinds(arc)
    navigation_path = arc / "inventory" / "navigation.json"
    try:
        navigation = json.loads(navigation_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        navigation = {"systems": {}}
    expected_module_dirs = {
        (system_slug, slugify(module_name))
        for system_slug, system in navigation.get("systems", {}).items()
        for module_name in system.get("modules", {})
    }
    actual_module_dirs = {
        (path.parents[2].name, path.parent.name)
        for path in module_docs
    }
    for system_slug, module_slug in sorted(expected_module_dirs - actual_module_dirs):
        errors.append(f"机械导航中的业务模块缺少文档：systems/{system_slug}/modules/{module_slug}/overview.md")
    for system_slug, module_slug in sorted(actual_module_dirs - expected_module_dirs):
        errors.append(
            f"systems/{system_slug}/modules/{module_slug} 是未纳入 module-map/navigation 的孤立模块；"
            "请迁移内容后移除或修正映射"
        )
    common_sections = [
        "阅读地图", "实现细节导航", "业务背景与用户价值", "业务术语与核心概念",
        "角色、权限与职责边界", "开发指南", "构建、测试与排障",
    ]
    frontend_sections = [
        "页面入口、路由与访问条件", "页面总体流程", "View 与重要组件结构",
        "状态、数据与副作用", "用户交互与关键前端逻辑", "接口协作", "业务规则与边界场景",
    ]
    backend_sections = [
        "业务用例与总体流程", "业务规则与关键分支", "接口目录", "接口与实现详解",
        "数据模型与持久化", "事务、一致性与并发", "依赖、事件与外部副作用",
        "配置、权限与运行约束",
    ]
    for path in module_docs:
        text = path.read_text(encoding="utf-8", errors="ignore")
        kind = kinds.get(path.parents[2].name, "general")
        required = common_sections + (frontend_sections if kind == "frontend" else backend_sections)
        for section in required:
            body = section_body(text, section)
            if not body:
                errors.append(f"{rel(path, repo)} 缺少章节：{section}")
            elif len(re.sub(r"\s+", "", body)) < 80:
                warnings.append(f"{rel(path, repo)} 章节内容过浅：{section}")
        compact_length = len(re.sub(r"\s+", "", text))
        if compact_length < 2200:
            warnings.append(f"{rel(path, repo)} 仅 {compact_length} 个非空白字符，难以作为新人开发手册")
        evidence = re.findall(r"`[^`\n]+[/\\][^`\n]+(?:#[A-Za-z_$][\w$]*)?`", text)
        if len(set(evidence)) < 5:
            warnings.append(f"{rel(path, repo)} 源码/测试证据少于 5 个，无法支撑完整业务说明")
        numbered_steps = re.findall(r"(?m)^\s*\d+[.)、]\s+", text)
        if len(numbered_steps) < 4:
            warnings.append(f"{rel(path, repo)} 缺少至少一条可执行的编号业务流程")
        if kind == "frontend":
            component_body = section_body(text, "View 与重要组件结构")
            if "|" not in component_body or ("├" not in component_body and "└" not in component_body and "```mermaid" not in component_body):
                warnings.append(f"{rel(path, repo)} 缺少组件树或重要组件职责表")
        else:
            rules_body = section_body(text, "业务规则与关键分支")
            if len(re.findall(r"(?m)^\|.*\|$", rules_body)) < 4:
                warnings.append(f"{rel(path, repo)} 缺少可核验的业务规则/关键分支表")
        module_topics = [topic for topic in path.parent.glob("*.md") if topic.name != "overview.md"]
        if len(module_topics) < 2:
            errors.append(f"{rel(path.parent, repo)} 只有 overview 或细节文档不足；每个模块至少需要 2 份实现细节文档")
        for topic in module_topics:
            if topic.name != "overview.md" and topic.name not in text:
                errors.append(f"{rel(path, repo)} 未链接同目录专题：{topic.name}")
        system_slug = path.parents[2].name
        module_slug = path.parent.name
        system_data = navigation.get("systems", {}).get(system_slug, {})
        module_entries = next(
            (
                entries for module_name, entries in system_data.get("modules", {}).items()
                if slugify(module_name) == module_slug
            ),
            [],
        )
        if kind == "backend":
            for route in backend_entrypoints(module_entries):
                if not any(route in topic.read_text(encoding="utf-8", errors="ignore") for topic in module_topics):
                    errors.append(f"{rel(path.parent, repo)} 缺少接口 `{route}` 的独立实现文档")
        elif kind == "frontend":
            page_paths = [
                item["path"] for item in module_entries
                if Path(item["path"]).suffix.lower() in {".vue", ".tsx", ".jsx"}
                or any(part in {"view", "views", "page", "pages"} for part in Path(item["path"]).parts)
            ]
            for page_path in page_paths:
                if not any(page_path in topic.read_text(encoding="utf-8", errors="ignore") for topic in module_topics):
                    errors.append(f"{rel(path.parent, repo)} 缺少页面 `{page_path}` 的独立实现文档")
    for path in topic_docs:
        text = path.read_text(encoding="utf-8", errors="ignore")
        compact_length = len(re.sub(r"\s+", "", text))
        if compact_length < 1200:
            warnings.append(f"{rel(path, repo)} 实现细节文档少于 1200 个非空白字符")
        evidence = re.findall(r"`[^`\n]+[/\\][^`\n]+(?:#[A-Za-z_$][\w$]*)?`", text)
        if len(set(evidence)) < 3:
            warnings.append(f"{rel(path, repo)} 实现细节文档源码/测试证据少于 3 个")
        if path.name.startswith(("interface-", "use-cases", "business-rules")):
            for section in [
                "业务场景与调用方", "请求、响应与业务语义", "完整实现链路",
                "关键业务逻辑与算法", "数据读写与副作用", "异常、错误码与可观测性",
                "测试与修改指南",
            ]:
                body = section_body(text, section)
                if not body:
                    errors.append(f"{rel(path, repo)} 缺少后端实现章节：{section}")
                elif len(re.sub(r"\s+", "", body)) < 100:
                    warnings.append(f"{rel(path, repo)} 后端实现章节过浅：{section}")
            if len(re.findall(r"(?m)^\s*\d+[.)、]\s+", text)) < 5:
                warnings.append(f"{rel(path, repo)} 完整实现链路少于 5 个可执行步骤")
            request_body = section_body(text, "请求、响应与业务语义")
            if len(re.findall(r"(?m)^\|.*\|$", request_body)) < 3:
                warnings.append(f"{rel(path, repo)} 缺少逐字段请求/响应业务语义表")
            chain_body = section_body(text, "完整实现链路")
            symbol_anchors = re.findall(r"`[^`\n]+[/\\][^`\n]+#[A-Za-z_$][\w$]*`", chain_body)
            if len(set(symbol_anchors)) < 2:
                warnings.append(f"{rel(path, repo)} 实现链路中少于 2 个文件#符号锚点")
        if path.name.startswith(("page-", "components-and-state")):
            for section in [
                "页面业务目标与用户", "View 编排与重要组件树", "首屏初始化流程",
                "用户操作与功能点", "状态、计算属性与生命周期",
                "API 协作与数据转换", "展示规则与边界场景", "测试与修改指南",
            ]:
                body = section_body(text, section)
                if not body:
                    errors.append(f"{rel(path, repo)} 缺少前端页面实现章节：{section}")
                elif len(re.sub(r"\s+", "", body)) < 100:
                    warnings.append(f"{rel(path, repo)} 前端页面实现章节过浅：{section}")
            component_body = section_body(text, "View 编排与重要组件树")
            if "├" not in component_body and "└" not in component_body and "```mermaid" not in component_body:
                warnings.append(f"{rel(path, repo)} 缺少页面组件树")
            if len(re.findall(r"(?m)^\|.*\|$", component_body)) < 3:
                warnings.append(f"{rel(path, repo)} 缺少重要组件职责与契约表")
            api_body = section_body(text, "API 协作与数据转换")
            if len(re.findall(r"(?m)^\|.*\|$", api_body)) < 3:
                warnings.append(f"{rel(path, repo)} 缺少逐接口前端协作与数据转换表")
            if len(re.findall(r"(?m)^\s*\d+[.)、]\s+", text)) < 4:
                warnings.append(f"{rel(path, repo)} 页面流程少于 4 个可执行步骤")
    for path in sorted(arc.rglob("*.md")):
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
    if errors or warnings:
        raise SystemExit(1)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init"); init.add_argument("--repo", required=True); init.set_defaults(func=command_init)
    scan = sub.add_parser("scan"); scan.add_argument("--repo", required=True); scan.add_argument("--update", action="store_true"); scan.set_defaults(func=command_scan)
    upgrade = sub.add_parser("upgrade-layout"); upgrade.add_argument("--repo", required=True); upgrade.set_defaults(func=command_upgrade_layout)
    feature = sub.add_parser("new-feature"); feature.add_argument("--repo", required=True); feature.add_argument("--title", required=True); feature.set_defaults(func=command_new_feature)
    archive = sub.add_parser("archive"); archive.add_argument("--repo", required=True); archive.add_argument("--feature", required=True); archive.add_argument("--summary", required=True); archive.add_argument("--files", default=""); archive.set_defaults(func=command_archive)
    sync = sub.add_parser("sync"); sync.add_argument("--repo", required=True); sync.add_argument("--since"); sync.set_defaults(func=command_sync)
    context = sub.add_parser("context"); context.add_argument("--repo", required=True); context.add_argument("--query", required=True); context.add_argument("--limit", type=int, default=3); context.set_defaults(func=command_context)
    doctor = sub.add_parser("doctor"); doctor.add_argument("--repo", required=True); doctor.add_argument("--strict", action="store_true", help="兼容参数；v5 始终执行严格检查"); doctor.set_defaults(func=command_doctor)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
