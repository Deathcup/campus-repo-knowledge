# 分层知识库结构规范

## 目录结构

```text
.repo-knowledge/
  INDEX.md
  systems/
    backend/
      overview.md
      modules/
        logs.md
        users.md
    frontend/
      overview.md
      modules/
        log-search.md
  features/
    YYYY-MM-DD-需求名/
      request.md
      spec.md
      implementation.md
      verification.md
  decisions/
    0001-决策标题.md
  inventory/
    repo-map.md
    navigation.json
    schema-version
  inbox/
    sync-YYYY-MM-DD-HHMMSS.md
```

允许使用实际部署单元或稳定边界替换 `backend`、`frontend`，例如 `gateway`、`worker`、`mobile`、`shared-sdk`。不要为了凑层级制造虚假的子系统。

## 导航职责

### `INDEX.md`：根总览

控制在约 300 行内，供人和 Agent 首次进入。必须包含：

- 项目用途的一段话摘要；
- 子系统表：名称、职责、代码范围、识别词、子系统总览链接；
- 跨系统主链路；
- 认证、权限、错误、日志等全局约束；
- 需求历史与长期决策入口；
- 无法路由时的机械地图入口。

根总览不得展开某个接口的完整实现。

### `systems/<子系统>/overview.md`：子系统总览

必须包含子系统边界、入口、主链路、共享约束，以及模块路由表。每个模块行至少有：

- 人能理解的一句话职责；
- HTTP 路径、RPC 名、事件名、页面路由、公开符号、业务别名等检索词；
- 模块独立文档链接。

如果用户可能用 `eslog`、`日志查询`、`/eslog/query` 三种方式提问，就把三者都写进日志模块的路由行。

### `systems/<子系统>/modules/<模块>.md`：模块独立文档

一个稳定业务能力一份文档。必须包含：

1. 一句话说明和职责边界；
2. 接口目录；
3. 每个接口的用途、参数、鉴权、返回、异常与实现链路；
4. 核心数据流与关键分支；
5. 数据模型、状态和持久化；
6. 配置、权限和外部依赖；
7. 修改指南与隐含约束；
8. 构建、测试和排障；
9. 关键文件、需求、决策和相邻模块链接；
10. 具体待确认问题。

接口实现链路至少精确到 `入口文件#符号 → 业务实现文件#符号 → 数据访问/外部调用文件#符号`。不能只列 Controller 文件。

## 模块划分规则

- 首选业务能力和稳定职责，如“日志查询”“账号权限”“订单结算”。
- 不把 controller、service、repository、components、views、api 当作最终业务模块；这些是技术层。
- 同一能力跨多个技术层时合并为一个模块文档。
- 前端和后端各自建模块文档，通过 API 契约互链，不合并成一份超长文档。
- 公共基础设施只有在确实具有独立契约和维护方式时作为模块，如“认证中间件”“消息总线”。
- 过大模块按可独立理解和变更的业务子能力拆分；过小模块合并到最接近的稳定能力。

## 其他目录

- `features/` 保存“为什么改、预期什么、最终如何、验证到哪”，不替代模块当前态文档。
- `decisions/` 只保存跨需求、长期有效且存在取舍的决策。
- `inventory/` 是机械事实和降级入口，不是人类阅读的首选。
- `inbox/` 是同步临时区；处理完必须记录去向，不能让它成为第二套正式知识库。

## 兼容旧版

旧版 `project.md` 内容按层级迁往根总览或对应子系统总览；旧版 `modules/*/overview.md` 按职责迁往模块独立文档。迁移期间可保留旧文件，但 `INDEX.md` 只链接新版路径。确认所有持久结论已迁移且无外部引用后再删除旧文件。

## 验收

运行：

```bash
python <skill>/scripts/repo_knowledge.py doctor --repo <repo> --strict
```

机械检查通过后仍需人工抽查：从一个自然语言问题开始，是否能只凭根总览选择子系统，只凭子系统总览选择模块，再从模块文档定位接口完整实现和最少源码证据。
