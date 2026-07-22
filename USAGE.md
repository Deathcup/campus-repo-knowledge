# Campus Repo Knowledge 使用说明

`campus-repo-knowledge` 在代码仓的 `.repo-knowledge/` 中建立一套面向团队成员和 Agent 的中文工程手册。它不只生成项目概览，而是为前端、后端等子系统建立总览，并为每个业务模块维护独立文档，记录接口和真实实现链路。

## 安装

```powershell
git clone https://github.com/Deathcup/campus-repo-memory.git "$env:USERPROFILE\.codex\skills\campus-repo-knowledge"
```

安装后在新任务中调用 `$campus-repo-knowledge`。

## 初始化示例

```text
请使用 $campus-repo-knowledge 初始化当前仓库。
按项目总览、子系统总览、业务模块独立文档建立分层知识库。逐个模块核对源码和测试，详细记录接口入口、参数与鉴权、核心调用链、数据访问、异常、配置和测试证据。文档要让没读过源码的人也能理解，不要只生成文件清单或待补充骨架。最后运行严格质量检查。
```

产物结构：

```text
.repo-knowledge/
  INDEX.md
  systems/
    backend/
      overview.md
      modules/
        logs.md
    frontend/
      overview.md
      modules/
        log-search.md
  features/
  decisions/
  inventory/
  inbox/
```

## 查询示例

```text
请使用 $campus-repo-knowledge 查询后端日志 eslog/query 接口怎么实现。
严格按 INDEX.md → 后端总览 → 日志模块文档 → 模块链接的源码与测试渐进读取，说明接口入口、鉴权、参数、调用链、查询实现、异常和测试证据。
```

查询时先读根总览判断子系统，再读该子系统总览判断模块，最后从模块文档定位实现。只有上层无法路由时才使用机械关键词检索；查清后应补回缺失导航。

## 维护示例

开发完成后：

```text
请使用 $campus-repo-knowledge 归档当前改动。结合最终 diff 和测试结果补全需求档案，更新受影响模块的接口与实现说明，并同步子系统和根总览。不要覆盖人工文档，完成后运行严格质量检查。
```

未知改动同步：

```text
请使用 $campus-repo-knowledge 从 HEAD~5 同步知识库。按子系统和业务模块聚类变更，区分代码事实与需求意图推断，更新模块当前态、历史需求和必要决策。
```

## 验收重点

- 根总览能明确选择前端、后端或其他子系统。
- 子系统总览能通过业务词、接口路径和代码别名定位模块。
- 每个业务模块都有独立文档，不以技术层目录充当模块。
- 具体接口能追踪到入口、核心业务实现、数据访问或外部调用及测试。
- 文档先讲业务行为，再给相对路径和符号证据。
- 没有坏链、空模块或无解释的“待补充”。

脚本只负责建立结构、发现候选、输出分层查询路线和执行质量检查；完整知识必须由 Agent 阅读源码、构建配置和测试后写成。
