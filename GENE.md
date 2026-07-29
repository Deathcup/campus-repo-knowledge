# Gene for campus-repo-knowledge

> **这是一个参考副本。** 真正起作用的是 `SKILL.md` 的内容——已从 3,153 tokens 缩减为 ~450 tokens 的混合方案（Gene 控制指令 + 关键结构规范）。原完整文档保留在 `references/FULL.md`。详见 `docs/what-is-gene.md`。

<strategy-gene>
Domain keywords: repo-knowledge, .repo-knowledge, 知识库, 代码文档, 业务模块, INDEX.md, overview.md, module-map, doctor

Summary: 在目标仓库建立分层中文知识库 (INDEX→子系统→模块→实现细节)，通过渐进式源码调查产出"让新人独立理解业务"的开发手册。

Strategy:
1. 判断场景:
   - .repo-knowledge/ 不存在 → 初始化
   - 用户询问代码/接口 → 分层查询 (INDEX→子系统overview→模块overview→实现文档→源码)
   - 开发完成 → 归档 (更新模块文档+总览+doctor)
   - 代码已变知识库落后 → 同步 (diff聚类→分片→更新→doctor)
2. 初始化步骤: init脚本 → 编辑module-map.json归并技术类到业务模块 → 分派子Agent按subagent-workflow.md调查 → 每模块至少overview+2份实现细节文档
3. 前端: 逐页面覆盖 View→组件树→状态→交互→API协作→边界
4. 后端: 逐接口覆盖 用例→规则分支→实现步骤→数据变化→事务/并发→副作用

AVOID:
- 禁止把 Controller/Service/Mapper/Repository 等技术层当作业务模块名
- 禁止把所有实现塞回 overview.md 不拆独立文档
- 禁止跳过渐进加载直接全局搜索源码
- 禁止保留 "待补充"/"待调查"/"TODO"/"TBD" 占位词
- 禁止用路由表/接口表/文件清单冒充知识文档
- 禁止在未阅读源码和测试的情况下写业务规则描述

Edge cases:
- module-map.json 存在技术层碎片 → 必须归并到业务模块
- doctor --strict 任何警告都视为失败 → 回源码修正
- 大型仓库按 subagent-workflow.md 分派
- v1/v2/v3 老格式 → 先迁移目录

Validation: python <skill>/scripts/repo_knowledge.py doctor --repo <repo> --strict
</strategy-gene>

## v2 实验结论

| 方案 | 注入 token | 模块归并 | 结构规范 | 评价 |
|------|:--:|:--:|:--:|------|
| 完整 SKILL.md | 3,153 | ✅ | ✅ | 太费 token |
| 纯 Gene | 280 | ✅ | ❌ 丢 module-map.json | 太简 |
| **混合方案（当前）** | **~450** | ✅ | ✅ | **最佳** |
