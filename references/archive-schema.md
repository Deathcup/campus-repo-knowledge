# 知识库结构规范

在代码仓根目录使用以下结构：

```text
.repo-knowledge/
  INDEX.md
  project.md
  inventory/
    repo-map.md
    module-map.json
    code-signals.json
  modules/
    <模块名>/
      overview.md
  features/
    YYYY-MM-DD-需求名/
      request.md
      spec.md
      implementation.md
      verification.md
  decisions/
    0001-决策标题.md
  inbox/
    sync-YYYY-MM-DD-HHMMSS.md
```

## INDEX.md

快速入口，尽量控制在 300 行以内。包含项目快照、阅读顺序、模块索引、需求历史、关键决策和未处理同步项。每一项都要有一句摘要和相对链接。

## project.md

记录仓库级长期知识：产品与领域、运行架构、入口、构建与测试命令、横切规则、数据/API/UI 契约、运维信息、已知风险和术语表。

## modules/<模块名>/overview.md

未来 Agent 理解一个子系统的起点。记录模块职责、关键文件、对外接口、数据流、现有行为、扩展点、测试、关联需求、关联决策和维护注意事项。代码事实必须给出相对路径作为证据。

## features/YYYY-MM-DD-需求名/

计划中或已完成的需求都使用同一结构：

- `request.md`：用户需求、问题与目标、范围、非目标、约束、待确认问题。
- `spec.md`：预期行为、受影响模块、输入输出、异常与边界、兼容性、验收条件。
- `implementation.md`：实现摘要、变更文件、设计说明、迁移或配置、后续事项。
- `verification.md`：自动化检查、手动检查、测试数据、已知缺口。

区分“用户已确认”“代码已验证”和“根据代码推断”。历史需求可以更正，但不要抹掉会影响后续维护的重要背景。

## decisions/

只记录长期有效、跨越单次需求的取舍。每个文件一个决策；重大反转用新记录取代旧记录，并互相链接。

```markdown
# NNNN 决策标题

- 状态：提议 | 已采纳 | 已取代
- 日期：YYYY-MM-DD
- 关联：相对链接

## 背景

## 决策

## 影响

## 考虑过的方案

## 后续事项
```

## inbox/

存放尚未整理的同步发现。它是临时收件箱，不是正式知识来源。处理后写明结论去了哪里、哪些问题仍待确认；稳定内容必须进入项目、模块、需求或决策文档。
