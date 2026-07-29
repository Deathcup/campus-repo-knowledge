# campus-repo-knowledge Skill 的 Gene 理论分析与改造方案

## 一、先回答：前面的实验是否贴合研发实际？

**坦诚地说，不完全贴合。** 前面的验证实验有以下几个不足：

### 问题 1：任务是合成的
5 个任务都是我为验证论文而编写的"标准编程题"——CSV 分析、API 客户端、格式转换器等。它们更像是 LeetCode 式的独立函数实现，而不是研发中真正遇到的"理解一个大型代码仓→定位业务逻辑→产出文档"这种复杂工作流。

### 问题 2：评估维度单一
用检查点 (checkpoint) 评分衡量代码功能完整性，但实际工作中更关心的是：
- 产出的知识文档是否准确反映了代码的真实行为？
- 文档是否让新人能独立理解和开发？
- 模型是否遵循了正确的调查路径而非跳步？

### 问题 3：Skill 和 Gene 的对比不够严格
我自己写的"Skill"约 1200 tokens，"Gene"约 330 tokens，但实际 production Skill（如 campus-repo-knowledge）是 ~33,000 tokens 的完整工程包。真正的挑战在于：**如何从 33K tokens 的完整工程知识中提取 300 tokens 的控制信号？**

---

## 二、campus-repo-knowledge 现状剖析

### 2.1 规模数据

| 组件 | 大小 | 估计 token | 类型 |
|------|------|-----------|------|
| SKILL.md | 12,612 bytes | ~3,153 | 主文档（混合型） |
| USAGE.md | 4,659 bytes | ~1,165 | 使用说明 |
| references/subagent-workflow.md | 11,983 bytes | ~2,995 | 参考-工作流 |
| references/writing-guide.md | 8,646 bytes | ~2,161 | 参考-写作规范 |
| references/archive-schema.md | 8,284 bytes | ~2,071 | 参考-归档结构 |
| references/module-research.md | 7,672 bytes | ~1,918 | 参考-模块调查 |
| references/language-hints.md | 2,306 bytes | ~576 | 参考-语言提示 |
| scripts/repo_knowledge.py | 64,711 bytes | ~16,177 | 工具脚本 |
| tests/test_repo_knowledge.py | 10,324 bytes | ~2,581 | 测试 |
| **总计** | **~131,197 bytes** | **~32,799 tokens** | |

### 2.2 SKILL.md 结构解剖

按论文的章节分解法分析 SKILL.md 的每个 section：

| Section | Token 估算 | 类型 | 论文对应 | 论文观察 |
|---------|-----------|------|---------|---------|
| Frontmatter (name/description) | ~150 | 元数据+概述 | Overview | **可能有害 (-4.7pp)** |
| 不可妥协的结果 (9条铁律) | ~500 | 质量要求/约束 | Overview/Pitfalls混合 | 约束有价值 |
| 任务路由 (6种场景) | ~200 | 路由逻辑 | Workflow | **核心控制信号** |
| 分层查询 (6步+示例) | ~400 | 操作流程 | Workflow | **核心控制信号** |
| 初始化/升级 (17步) | ~900 | 详细流程 | Workflow | **核心控制信号** |
| 增量需求 (5步) | ~150 | 操作流程 | Workflow | 有效 |
| 完成后归档 (6步) | ~200 | 操作流程 | Workflow | 有效 |
| 未知改动同步 (6步) | ~200 | 操作流程 | Workflow | 有效 |
| 内部命令 (7条) | ~250 | CLI 参考 | API Notes | 中性/辅助 |
| 按需读取参考 | ~100 | 引用索引 | Reference | 中性 |

### 2.3 论文视角的诊断

根据论文发现的规律，campus-repo-knowledge 的 SKILL.md 存在以下结构性问题：

1. **Frontmatter description 过于冗长** (150 tokens)。论文发现 Overview 型内容 (-4.7pp) 不仅无用，反而可能干扰模型的任务路由判断。当前的 description 是一个长达 150+ 字的自然语言段落，包含了太多了"什么时候用"的上下文。

2. **"不可妥协的结果" (9条铁律) 位置过于靠前**。这些是约束条件（类似论文的 AVOID），但它们被嵌入在散文段落中，而非结构化的 AVOID 信号。论文发现结构化 AVOID 的效果优于平铺在散文中。

3. **多个工作流 (初始化、增量、归档、同步) 平铺在同一个文档中**。没有明确的"路由→匹配→注入"机制。模型需要通读全部才能判断当前属于哪个场景。

4. **内部命令列表作为 Reference 存在**，符合论文对辅助材料 (API Notes) 的中性判断。但其后的 `references/` 按需加载设计是正确的（与论文"文档材料附加回 Gene 会削弱效果"的发现一致）。

5. **SKILL.md 混合了控制指令和参考文档**。按照论文观点：控制指令应紧凑 (~300 tokens)，参考文档应按需加载。

---

## 三、Gene 改造方案

### 3.1 核心设计原则

基于论文发现，改造应遵循：

1. **控制与文档分离**: Gene（控制层/~300 tokens）总是在上下文；完整 SKILL.md（文档层/~3000 tokens）按需加载
2. **结构化 AVOID**: 用显式的 AVOID 信号替代散文式的"不可妥协结果"
3. **场景路由**: 用关键词匹配自动路由到正确的操作模式
4. **策略优先**: 告诉模型"怎么做"和"不要做什么"，而非"这是什么"

### 3.2 改造后的 Gene（控制层，~280 tokens）

```yaml
# Gene for campus-repo-knowledge
# 这个 Gene 在每次调用 skill 时自动注入，约 280 tokens

<strategy-gene>
Domain keywords: repo-knowledge, .repo-knowledge, 知识库, 代码文档, 业务模块, INDEX.md, overview.md, module-map

Summary: 在目标仓库建立和维护分层中文知识库（INDEX→子系统→模块→实现细节），
通过渐进式源码调查产出"让新人能独立理解业务"的开发手册。

Strategy:
1. 判断场景路由:
   - 不存在 .repo-knowledge/ → 初始化/升级
   - 用户询问代码/接口 → 分层查询
   - 开发完成/代码变更 → 归档或同步
2. 分层查询必须严格渐进: INDEX.md → systems/<sub>/overview.md → modules/<mod>/overview.md → 实现文档 → 源码
3. 初始化时: 先运行 init 脚本 → 编辑 module-map.json 归并技术类到业务模块 → 分派子 Agent 并行调查各模块 → 每个模块至少 overview.md + 2 份实现细节文档
4. 归档/同步后必须运行 doctor --strict，直到"错误 0，警告 0"

AVOID:
- 禁止把 Controller/Service/Mapper/Repository 等技术层当作业务模块
- 禁止把多个模块的实现平铺在一个 overview.md 里
- 禁止跳过 INDEX→子系统总览→模块 overview 的渐进加载，直接全局搜索源码
- 禁止在文档中保留 "待补充"/"待调查"/"TODO"/"TBD" 占位词
- 禁止用路由表/接口表/类名列表/文件清单冒充知识文档
- 禁止在未阅读源码和测试的情况下编写业务规则描述

Edge cases:
- module-map.json 中若存在技术层碎片模块名→必须归并到业务模块
- doctor --strict 的任何警告都视为失败→必须回源码修正
- 大型仓库按 subagent-workflow.md 分派，主 Agent 负责合并和冲突处理
- v1/v2/v3 老版本格式→先迁移目录再升级(v4→补细节文档)

Validation: python <skill>/scripts/repo_knowledge.py doctor --repo <repo> --strict
</strategy-gene>
```

### 3.3 与原始 SKILL.md 的对比

| 维度 | 原始 SKILL.md | 改造后 Gene |
|------|--------------|------------|
| Token 数 | ~3,153 | ~280 |
| Token 节省 | — | **91.1%** |
| 结构 | 混合（概述+流程+参考） | 纯控制（路由+策略+AVOID） |
| AVOID 信号 | 嵌入在 9 条"铁律"散文中 | 6 条显式结构化 AVOID |
| 场景路由 | 自然语言段落 | 关键词匹配→分支 |
| 文档层 | 同一文件内 | 独立按需加载 |
| 可匹配性 | 需要全文阅读判断 | signals_match 字段直接匹配 |

### 3.4 完整的改造架构

```
campus-repo-knowledge/
├── SKILL.md              # 完整文档（保持不动，服务人类）
├── GENE.md               # 新增: 控制层 Gene (~280 tokens)
├── USAGE.md              # 保持
├── references/           # 按需加载的参考文档（保持）
│   ├── archive-schema.md
│   ├── module-research.md
│   ├── writing-guide.md
│   ├── language-hints.md
│   └── subagent-workflow.md
├── scripts/              # 工具脚本（保持）
└── tests/                # 测试（保持）
```

推理时加载策略：
1. **始终注入**: GENE.md (~280 tokens)
2. **按需加载**: SKILL.md 仅在人类需要完整阅读时加载，或在 Gene 不足以路由时加载
3. **条件加载**: references/ 按 Gene 中的"按需读取参考"表按条件加载

---

## 四、预期收益（基于论文数据推算）

### 4.1 Token 成本

| 场景 | 当前 (全量加载) | 改造后 (Gene only) | 节省 |
|------|----------------|-------------------|------|
| 每次 skill 调用 | ~3,153 tokens | ~280 tokens | **91.1%** |
| 需要 1 个 reference | ~3,153 + ~2,000 | ~280 + ~2,000 | 29.5% |
| 全量 (含所有 refs) | ~32,799 tokens | ~32,799 tokens | 0% (全量时相同) |

### 4.2 基于论文的性能推算

论文数据：
- 完整 Skill (~2,500 tokens): **-1.1pp** vs 基线
- Gene (~230 tokens): **+3.0pp** vs 基线
- 净差距: **4.1pp**

如果 campus-repo-knowledge 遵循相似规律：
- 当前 3,153 token SKILL.md → 推测产生类似甚至更严重的信号稀释
- 280 token Gene → 推测提供更干净的初始控制信号
- 特别是在**任务路由**环节——当前需要读完整个 SKILL.md 才能判断该走初始化/查询/归档/同步哪条路径；Gene 用 3 行关键词匹配立即路由

---

## 五、关键风险与论文告诫

### 5.1 论文明确标注的外推风险

论文在 skill2gep README 中诚实声明：
> "Gene is better than Skill" is not the same as "skill2gep reliably produces high-quality Genes."

> The paper's empirical scope is narrow: 45 scientific code-solving scenarios with Gemini 3.1. Claims about other agent domains (web automation, long tool chains, multi-agent negotiation, human support workflows) are **extrapolation**.

campus-repo-knowledge 的领域（代码仓知识管理、多步骤 agent 工作流、文档产出质量）与论文验证的领域（科学代码求解）**完全不同**。Gene 理论在此领域的有效性是**待验证的假设**。

### 5.2 Gene 不能替代 Skill

论文明确：Skills 和 Genes 不是替代关系。Skill 服务人类，Gene 服务模型。我们不应删除 SKILL.md，而是在其基础上增加 GENE.md 作为模型控制层。

### 5.3 质量依赖来源

Gene 的质量取决于从中提取的 Skill 的质量。campus-repo-knowledge 的 SKILL.md 质量很高（结构清晰、场景覆盖完整），所以提取的 Gene 质量也应该较高。

---

## 六、建议的验证方案

与其用合成任务验证，不如在实际工作中做 A/B 对比：

### 方案：同任务双轨对比

1. 选一个真实仓库（如 campus-repo-knowledge 自己的代码仓）
2. 分别用"原始 SKILL.md"和"GENE.md + 按需 reference"初始化知识库
3. 对比指标：
   - 完成时间
   - Token 消耗
   - doctor --strict 首次通过率
   - 模块深度（每个模块的文档数量和章节完整性）
   - 占位词残留数量

这会是一个**远比合成任务更有说服力**的验证。

---

*分析日期: 2026-07-29*
