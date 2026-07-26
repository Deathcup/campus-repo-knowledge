# Campus Repo Knowledge 使用说明

`campus-repo-knowledge` 在代码仓的 `.repo-knowledge/` 中建立一套面向团队成员和 Agent 的中文开发手册。目标不是“告诉你代码在哪”，而是让只懂开发语言、第一次接触服务的人仅凭文档理解一个业务，并能安全地开始开发。

## 安装

```powershell
git clone https://github.com/Deathcup/campus-repo-knowledge.git "$env:USERPROFILE\.codex\skills\campus-repo-knowledge"
```

安装后在新任务中调用 `$campus-repo-knowledge`。

## 初始化示例

```text
请使用 $campus-repo-knowledge 初始化当前仓库。
按项目总览、子系统总览、业务模块开发手册建立分层知识库。生成时完整调查每个模块，不限制 token：前端写清用户流程、根 View、重要组件树和职责、状态、交互、API 协作与边界；后端写清业务用例、规则分支、实现步骤、查询/计算、数据变化、事务并发、外部副作用与失败恢复。加入针对当前仓库的开发指南和测试排障方法。不要把路由、接口表、类名或文件清单当成完成。最后运行 doctor --strict，并仅凭文档做新人上手验收。
```

产物结构：

```text
.repo-knowledge/
  INDEX.md
  systems/
    backend/
      overview.md
      modules/
        logs/
          overview.md
          business-rules.md
          interface-query.md
          interface-export.md
          development.md
    frontend/
      overview.md
      modules/
        log-search/
          overview.md
          page-list.md
          page-detail.md
          components-and-state.md
          development.md
  features/
  decisions/
  inventory/
    module-map.json
  inbox/
```

## 查询示例

```text
请使用 $campus-repo-knowledge 查询后端日志 eslog/query 接口怎么实现。
严格按 INDEX.md → 后端总览 → 日志模块开发手册渐进读取。先说明该业务服务谁、完整成功/失败流程和关键规则，再说明 eslog/query 的条件规范化、权限范围、查询构造、数据映射、异常、性能与测试。仅在核对文档新鲜度时打开手册链接的源码。
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
- `inventory/module-map.json` 已把 Controller、Service、Mapper 等机械候选归并为稳定业务模块，没有技术层碎片模块。
- 每个业务模块都有独立文档，不以技术层目录充当模块。
- 每个业务模块都有自己的目录，至少包含 `overview.md` 和两份实现细节文档；只有 overview 视为失败。
- 后端每个重要接口、消费者、任务或用例有独立实现文档；前端每个列表页、详情页、编辑页或独立 View 有独立页面文档。
- `overview.md` 的实现细节导航能把问题精确路由到对应 `interface-*`、`use-case-*`、`page-*` 或 `feature-*` 文档。
- 前端能看懂页面总体流程、根 View 如何编排、重要组件分别做什么、状态和 API 如何流动。
- 后端能看懂业务用例、关键规则为何触发、核心计算/查询、数据变化、事务并发和副作用。
- 文档先讲业务和规则，再给相对路径与符号证据；接口入参出参不能代替实现说明。
- 新人能根据“开发指南”规划一个相邻改动，并知道如何运行、测试和排障。
- 最终全库没有 `待补充`、`待调查`、`待核对`、`TODO`、`TBD` 或模板变量。
- `doctor --strict` 输出“错误 0，警告 0”；v5 中即使不写 `--strict`，任何警告也会导致失败。

脚本只负责建立结构、发现候选、输出分层查询路线和执行质量检查；完整知识必须由 Agent 阅读源码、构建配置和测试后写成。
