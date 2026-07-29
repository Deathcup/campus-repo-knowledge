# 什么是 Gene？—— 从概念到实践

## 一句话回答

**Gene 不是 Skill 的替代品，而是 Skill 的"模型控制层"。** Skill 写给人看，Gene 写给模型看。两者共存，各司其职。

---

## 一、Gene 不是什么

在理解 Gene 是什么之前，先澄清三个常见的误解：

| 误解 | 事实 |
|------|------|
| ❌ Gene 是"缩短版的 Skill" | Gene 是**不同的抽象**。Skill 按文档逻辑组织，Gene 按控制逻辑组织。把 Skill 压缩成 300 字不等于 Gene。 |
| ❌ Gene 是 Skill 的"摘要"或"TL;DR" | Gene 的关键字段（尤其是 AVOID 和 strategy）在 Skill 中可能根本没有对应文本，需要从失败经验中**蒸馏**出来。 |
| ❌ Gene 可以替代 Skill | 论文明确：Skills 服务于人类（阅读、教学、审查、归档），Genes 服务于模型（推理时行为控制）。删掉 Skill 只留 Gene，人类就看不懂了。 |

---

## 二、Gene 是什么

Gene 是一个**紧凑的、结构化的、控制导向的经验表示**。它从先前的经验（Skill 文档、执行轨迹、失败记录）中蒸馏而来，在推理时作为模型的行为控制信号注入。

### 2.1 形式定义

论文给出的形式定义：

```
Gene = (signals_match, summary, strategy, AVOID, constraints, validation)
       └─匹配触发──┘ └─────┘ └──────┘ └─────┘ └──────────┘ └──────────┘
```

| 字段 | 作用 | 示例 |
|------|------|------|
| **signals_match** | 关键词/触发条件，决定这个 Gene 何时被激活 | `csv, peak detection, find_peaks, scipy` |
| **summary** | 一句话概述，让模型快速理解这个 Gene 的用途 | `检测多传感器 CSV 数据中的峰值并导出分析结果` |
| **strategy** | 有序的策略步骤（3-8 条），核心控制逻辑 | `1. 用 argparse 解析 CLI 2. 用 pandas 加载并验证列...` |
| **AVOID** | 必须规避的常见错误。**这是 Gene 最有价值的字段** | `不要把 find_peaks 的索引直接当时间戳` |
| **constraints** | 可选的执行约束 | `超时 120s` |
| **validation** | 可选的验证钩子 | `python doctor --strict` |

### 2.2 一个完整的 Gene 实例

```xml
<strategy-gene>
Domain keywords: employee, 入职, 工号生成, 身份证校验, 考勤组关联
Summary: 为新员工创建档案，自动生成工号并关联默认考勤组
Strategy:
1. Controller 层先做身份证唯一性预检（existsByIdCard），失败立即抛 IllegalArgumentException
2. 进入 @Transactional 服务层：取当前年月 → nextEmployeeSeq 行锁取序号 → 拼接工号 EMP+yyyyMM+4位序号
3. 设 status=ACTIVE, hireDate=今天
4. employeeRepository.save → attendanceGroupRepository.addMember
5. AVOID: 不要在 Controller 层打开事务——身份证预检应快速失败，事务只包服务层
6. AVOID: 不要把工号序号生成放在事务外——并发入职会导致工号重复
Edge cases: 身份证重复→400, 考勤组不存在→事务回滚, 并发入职→行锁串行化
Validation: 验证生成的工号匹配正则 EMP\d{6}\d{4}，status=ACTIVE
</strategy-gene>
```

### 2.3 Gene 的四个核心特征

1. **控制导向而非文档导向**：Gene 的目标不是"让人看懂"，而是"让模型做对"。每一行都是可执行的指令或禁止项。

2. **AVOID 是核心**：论文发现，"仅失败警告"条件（+4.6pp）优于"策略+失败混合"条件（+2.0pp）。**告诉模型不要做什么，比告诉它要做什么更有效。**

3. **结构化而非散文化**：论文发现相同的经验内容，展平为散文后优势消失（54.0% → 50.5%）。结构化的字段本身就是性能因素。

4. **可进化**：Gene 是 GEP 进化协议中的原子单元。失败的执行会蒸馏为新的 AVOID 条目，验证通过后固化进 Gene。

---

## 三、Gene vs Skill：系统对比

### 3.1 根本差异

| 维度 | Skill（文档型） | Gene（控制型） |
|------|---------------|---------------|
| **设计对象** | 人类读者 | 语言模型（推理时） |
| **组织逻辑** | 文档逻辑（概述→工作流→示例→API 参考） | 控制逻辑（匹配→策略→规避→验证） |
| **目标** | 知识传递、教学、归档 | 行为控制、错误预防、信号传递 |
| **典型规模** | 1,000-3,000+ tokens | 200-500 tokens |
| **内容密度** | 低（大量解释性、背景性文字） | 高（每行都是可执行指令或禁止项） |
| **更新方式** | 人工编写、按需补充 | 从失败经验中蒸馏、验证后固化 |
| **可组合性** | 可以堆叠（但论文发现堆叠有害） | 单次推理用单个最匹配的 Gene |

### 3.2 论文的关键数据

| 条件 | Token 数 | 平均性能 | vs 基线 |
|------|---------|---------|---------|
| **完整 Skill** | ~2,500 | 49.9% | **-1.1 pp** (反而更差) |
| 仅 Skill-Workflow | ~600 | 52.5% | +1.5 pp |
| 仅 Skill-Overview | ~500 | 46.3% | **-4.7 pp** (严重有害) |
| **Gene** | ~230 | **54.0%** | **+3.0 pp** |
| Gene + API 文档 | ~800 | 51.5% | +0.5 pp (添加文档削弱了 Gene) |
| Gene (展平为散文) | ~230 | 50.5% | -0.5 pp (丢失结构化优势) |

核心结论：
- **Skill 的 Overview（概述性描述）是有害的**（-4.7pp）
- **Gene 加上文档材料后效果反而下降**（+3.0 → +0.5）
- **同样的内容，结构化比散文高 3.5pp**（54.0% vs 50.5%）

### 3.3 用人话总结

> **Skill 是一本教科书**——有目录、有背景介绍、有示例练习、有附录参考。给学生看很好，但考试时带整本教科书进场反而翻不过来。
>
> **Gene 是一张作弊小抄**——只有关键词、关键公式、常见错误提醒。考试时扫一眼就能用，不占地方。

两者各有各的用途。你不能把小抄当教材（人类学不会），也不该把教材当小抄（模型用不好）。

---

## 四、为什么需要 Gene？

### 4.1 当前 Skills 的问题

当前主流 agent 框架（Claude Code、Cursor、OpenCode 等）的 Skill 本质上是 **Markdown 文档包**：

```
skill/
├── SKILL.md          # 主文档：概述 + 工作流 + 示例 + API 参考
├── references/       # 补充参考材料
└── scripts/          # 工具脚本
```

当你调用一个 Skill 时，整个 `SKILL.md` 的内容被注入到模型的上下文窗口中。论文指出这种做法的三个问题：

1. **信号稀释**：2,500 tokens 中只有约 600 tokens 的工作流部分真正有用，其余（概述、API 参考等）是噪声
2. **强模型退化**：强模型（Pro）使用 Skill 后性能从 60.1% 降到 50.7%（-9.4pp），因为多余的文字干扰了模型自身的判断
3. **积累恶化**：每次失败后追加更多文档，控制信号越来越稀，形成负循环

### 4.2 Gene 的解决方式

Gene 把"模型需要知道的"和"人类需要知道的"分开：

```
推理时的上下文窗口：
┌──────────────────────────────────────────┐
│ GENE.md (~280 tokens)    ← 始终在窗口中  │
├──────────────────────────────────────────┤
│ SKILL.md                 ← 按需加载       │
│ references/*.md          ← 按需加载       │
│ 源码/上下文               ← 任务相关       │
└──────────────────────────────────────────┘
```

---

## 五、当前 Agent 框架能否直接使用 Gene？

### 5.1 现状：完全兼容，无需改造

Gene 的本质是一个**结构化的 prompt 片段**。任何能注入 system prompt 或 skill 指令的 agent 框架都可以直接使用 Gene。

| 框架 | 如何使用 Gene |
|------|-------------|
| **Claude Code** | 将 `GENE.md` 放在 skill 目录中，作为 skill 加载时优先注入的指令。或直接替换 SKILL.md 中注入模型的 prompt 部分 |
| **Cursor** | 在 `.cursor/skills/` 目录中，`GENE.md` 可以和 `SKILL.md` 共存。Cursor 加载 skill 时可以选择先注入 Gene |
| **OpenCode** | OpenCode 的 skill 机制类似，Gene 可以作为一个独立的 skill 层存在 |
| **GitHub Copilot** | 将 Gene 内容整合到 Copilot 的自定义指令中 |
| **任意 LLM 应用** | 直接将 `<strategy-gene>` 块作为 system message 注入 |

### 5.2 实践：三种集成模式

**模式 A：替换模式（最简单）**
把 Gene 作为 Skill 调用时注入模型的那部分 prompt。
```
原来: system_prompt = SKILL.md (3,000 tokens)
改为: system_prompt = GENE.md (280 tokens)
```
SKILL.md 仍然保留在文件系统中，人类看；模型只看 Gene。

**模式 B：分层模式（推荐）**
Gene 始终注入，Skill 按需检索。
```
始终注入: GENE.md → 路由 + AVOID + 核心策略
按需检索: SKILL.md sections → 只在需要详细参考时加载
```

**模式 C：自动蒸馏模式（未来）**
使用 skill2gep 适配器，从 Skill + 执行证据自动生成 Gene。
```bash
evolver skill2gep ./path/to/skill --execution=./execution-trace.json
```

### 5.3 立即可做的事

对于 campus-repo-knowledge，我已经在 `GENE.md` 中准备好了 Gene。要在 Claude Code 中使用它：

1. **让 Claude Code 优先加载 GENE.md**：在 `SKILL.md` 的 frontmatter 中添加一个 `gene_file` 字段，或修改调用逻辑让 GENE.md 的内容先于完整的 SKILL.md 注入

2. **或者直接替换注入内容**：目前当用户调用 `$campus-repo-knowledge` 时，Claude Code 会把整个 SKILL.md 注入上下文。可以改为先注入 GENE.md（280 tokens），只有当 Gene 不足以路由时才加载完整的 SKILL.md

3. **渐进式采用**：不需要一次性改造所有 Skills。先选 1-2 个高频 Skill 添加 Gene，观察效果。

---

## 六、Gene 的适用范围与局限

### 6.1 适合用 Gene 的场景

- ✅ 有明确步骤的**操作性任务**（如"为仓库初始化知识库"）
- ✅ 有已知**常见错误模式**的任务（AVOID 信号价值高）
- ✅ 被**高频调用**的 Skill（节省的 token 累积效应明显）
- ✅ 有多条执行**路径/场景**需要路由的 Skill

### 6.2 不太适合用 Gene 的场景

- ❌ **纯知识查询**类 Skill（如"某 API 的参数列表"），不需要策略控制
- ❌ **创意性**任务（没有"正确做法"）
- ❌ **一次性**任务（蒸馏的成本 > 收益）

### 6.3 论文明确标注的外推风险

论文作者诚实声明：
> 论文在 45 个科学代码求解场景上验证了 Gene vs Skill。对 web 自动化、长工具链、多 agent 协商、人工支持工作流等领域的推广是**外推假设**。

我们的 campus-repo-knowledge 实验是这一外推的初步验证，结果支持 Gene 在"代码仓知识管理"领域的有效性，但需要更多场景的验证。

---

## 七、总结

| 问题 | 答案 |
|------|------|
| Gene 是什么？ | 紧凑的、结构化的、控制导向的模型行为指令 |
| Gene 是 Skill 的替代品吗？ | 不是。Skill 给人看，Gene 给模型看，共存 |
| Gene 和 Skill 的核心区别？ | Skill = 教科书（知识传递），Gene = 小抄（行为控制） |
| 为什么需要 Gene？ | 完整 Skill 的文档信号会被稀释，甚至拖慢强模型 |
| 现有框架能用吗？ | 能。Gene 就是一段结构化 prompt，任何框架都能注入 |
| 怎么开始？ | 选一个高频 Skill，提取策略 + AVOID，写出 Gene，A/B 对比 |

---

*参考论文: Wang, Ren, Zhang. From Procedural Skills to Strategy Genes (arXiv:2604.15097, 2026)*
