---
name: campus-repo-knowledge
description: 在目标仓库建立和维护分层中文知识库。详细文档见 references/FULL.md
---

## 策略基因 (Strategy Gene)

<!-- 模型优先读取此 section。约 500 tokens。原理见 docs/what-is-gene.md -->

**触发词**: repo-knowledge, .repo-knowledge, 知识库, INDEX.md, module-map, doctor

**场景路由**:
- .repo-knowledge/ 不存在 → 初始化
- 用户问代码/接口 → 分层查询（INDEX → 子系统 overview → 模块 overview → 实现文档 → 源码）
- 开发完成 → 归档（更新模块文档 + 两级总览 + doctor --strict）
- 代码变更 → 同步（diff 聚类 → 分片 → 更新 → doctor）

**初始化要点**:
1. 运行 `init` 脚本 → 编辑 `inventory/module-map.json` 把 Controller/Service/Mapper 等技术类归并到业务模块
2. 每个业务模块独立目录，至少 `overview.md` + 2 份实现细节文档
3. 后端每个 HTTP 接口/消费者/定时任务独立文档（按 "方法 + 完整路径" 区分）
4. 前端每个列表页/详情页/编辑页独立文档
5. 回填子系统总览 → 回填根总览 → `scan --update` → `doctor --strict`（警告即失败）

**怎么做（后端）**:
- 从 HTTP 入口追到 Service → 领域规则 → Repository → 外部依赖
- 解释每条规则的触发条件、完整步骤、数据变化、事务/并发/副作用
- 包含逐字段业务语义表 + 至少两个 `文件#符号` 锚点

**怎么做（前端）**:
- 从路由/首屏追到 View → 组件树 → composable/store → API 客户端
- 解释用户流程、组件职责/契约、状态生命周期、交互分支

**不要做**:
- 不要把 Controller/Service/Mapper/Repository 等技术层目录名当业务模块名
- 不要把多个模块的实现平铺在一个 overview.md 里
- 不要跳过渐进加载直接全局搜索源码
- 不要保留 "待补充"/"待调查"/"TODO"/"TBD" 占位词
- 不要用路由表/接口表/类名列表/文件清单冒充知识文档
- 不要在未阅读源码和测试的情况下写业务规则描述

**目录规范**:
```
.repo-knowledge/
  INDEX.md                          # 系统总览 + 子系统路由
  systems/<子系统>/overview.md       # 业务地图 + 模块路由 + 检索词
  systems/<子系统>/modules/<模块>/    # 每个业务模块独立目录
    overview.md                     # 模块边界 + 规则摘要 + 实现导航
    interface-{method}-{name}.md    # 后端接口详情
    page-{name}.md                  # 前端页面详情
  inventory/module-map.json         # 技术类→业务模块映射
```

**验证**: `python <skill>/scripts/repo_knowledge.py doctor --repo <repo> --strict`

---

> 📖 **人类读者**: 本文档是为模型优化的执行摘要。完整的教学级文档见 [references/FULL.md](references/FULL.md)。
> 📖 **原理说明**: 为什么这样组织 SKILL.md？见 [docs/what-is-gene.md](docs/what-is-gene.md)。
