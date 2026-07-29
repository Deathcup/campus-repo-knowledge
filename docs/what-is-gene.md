# 什么是 Gene？—— 兼答"现有 agent 架构下怎么落地"

## 先直面核心问题

你提出的疑问完全正确：

> "把 Gene 写在 SKILL.md 开头，但 agent 还是会把整个 SKILL.md 全部注入模型——那 Gene 不是白加了吗？"

**是的。如果 SKILL.md 仍然包含全部正文，在开头加一个 Gene section 没有意义。** 模型还是会读完 3,000+ tokens，控制信号照样被稀释。论文的数据说的很清楚——完整 Skill 包是 -1.1pp，只有当你**只注入** compact 指令时才有 +3.0pp。

所以真正的问题是：**在不改造 agent 架构的前提下，怎么让模型只读到 compact 指令？**

---

## 一、诚实答案：把 SKILL.md 本身变成 Gene

当前所有 agent 框架的约定是：**调用 skill 时，加载 SKILL.md 的内容注入模型**。

那就利用这个约定——**让 SKILL.md 就是 Gene，把详细文档移到别处**：

```
改造前:                              改造后:
campus-repo-knowledge/               campus-repo-knowledge/
├── SKILL.md    ← 3,153 tokens       ├── SKILL.md    ← ~450 tokens (Gene + 结构规范)
│   (模型每次被注入 3,153 tokens)     │   (模型每次被注入 ~450 tokens)
├── USAGE.md                         ├── USAGE.md
└── references/                      ├── references/
    ├── archive-schema.md                ├── archive-schema.md
    ├── module-research.md               ├── module-research.md
    ├── writing-guide.md                 ├── writing-guide.md
    ├── language-hints.md                ├── language-hints.md
    └── subagent-workflow.md             ├── subagent-workflow.md
                                         └── FULL.md  ← 原 SKILL.md 完整版
                                                        (人类学习时看)
```

**关键变化**：
- `SKILL.md` 从 3,153 tokens 缩减为 ~450 tokens 的混合方案
- 原完整内容移到 `references/FULL.md`，人类需要时手动打开看
- Agent 框架无感知——它照常加载 SKILL.md，只是内容变短了

---

## 二、为什么这是对的

### 2.1 论文数据支持

| 模型看到的内容 | Token 数 | 效果 |
|--------------|---------|------|
| 完整 Skill 文档 | ~2,500 | **-1.1 pp** |
| 无引导 | 0 | 0（基线） |
| 仅 compact 指令 | ~230 | **+3.0 pp** |

关键：compact 指令**单独注入**时效果最好。论文还发现给 compact 指令加上 API 文档后效果反而下降（+3.0 → +0.5）。所以 SKILL.md 必须**只**包含 compact 指令，不能夹带详细文档。

### 2.2 模型行为解释

论文 Skill Probe 发现：文档中的 Overview 型描述**本身就是有害的**（-4.7pp）。为什么？因为描述性文字会改变模型的"思维框架"——模型读了一大段"这个技能是干什么的、适用于什么场景、有什么背景"之后，反而可能偏离了任务本身的最佳执行路径。

紧凑的策略指令则不同。它不给模型"解释"，只给"指令"。就像一个有经验的同事拍你肩膀说"做这3步，注意别踩那两个坑"，这比给你一本操作手册有效得多。

---

## 三、Gene 到底是什么

### 3.1 一句话

**Gene 是 Skill 的模型执行摘要。把 SKILL.md 改造为 Gene 控制指令 + 关键结构规范的混合方案（~450 tokens），完整文档移入 references/。**

### 3.2 和 Skill 的关系

| | Skill（广义） | SKILL.md（改造后） | 详细文档 |
|------|------|------|---|
| **是什么** | 这个能力的完整知识包 | Gene = compact 控制指令 | 原来的 SKILL.md 完整版 |
| **写给谁** | — | **模型**（推理时注入） | **人类**（学习、审查、归档） |
| **何时读** | — | 每次调用 skill 时 | 需要深入理解时手动打开 |
| **文件** | 整个目录 | `SKILL.md`（~280 tokens） | `references/FULL.md` |
| **本质** | 能力单元 | **能力的模型控制接口** | 能力的文档化知识 |

### 3.3 和"缩短版 Skill"的区别

这不是把 SKILL.md 删减到 280 tokens。Gene 的增加和删减逻辑不同：

| 操作 | 说明 |
|------|------|
| **删掉** | 概述、背景、教学性解释、代码示例、API 参数列表、安装说明——这些是给人看的 |
| **保留/强化** | 策略步骤、场景路由逻辑、触发关键词 |
| **新增** | AVOID 信号——这在原来的 Skill 中可能根本没有，需要从失败经验中蒸馏 |

### 3.4 一个完整的改造例子

**改造前（SKILL.md，3,153 tokens）**：
```
---
name: campus-repo-knowledge
description: 为代码仓生成、查询和维护面向人类与 Agent 的实现级分层中文知识库...
---

# Campus Repo Knowledge

在目标仓库维护 .repo-knowledge/...

## 不可妥协的结果
1. 建立严格的分层导航...
2. 为每个稳定业务模块建立独立目录...
（9 条铁律，约 500 tokens）

## 任务路由
（约 200 tokens）

## 分层查询
（约 400 tokens）

## 初始化/升级
（17 步详细流程，约 900 tokens）
...（还有更多）
```

**改造后（SKILL.md，~450 tokens，混合方案）**：
```markdown
---
name: campus-repo-knowledge
description: 在目标仓库建立和维护分层中文知识库。详细文档见 references/FULL.md
---

## 策略基因

**触发词**: repo-knowledge, .repo-knowledge, 知识库, INDEX.md, module-map, doctor

**场景路由**:
- .repo-knowledge/ 不存在 → 初始化
- 用户问代码/接口 → 分层查询（INDEX→子系统→模块→实现文档→源码，禁止跳步）
- 开发完成 → 归档
- 代码变更 → 同步

**初始化要点**: ...（5 步核心流程）
**怎么做（后端/前端）**: ...（各 2-3 条原则）
**不要做**: ...（6 条 AVOID）

**目录规范**:
.repo-knowledge/
  INDEX.md
  systems/<子系统>/overview.md
  systems/<子系统>/modules/<模块>/
    overview.md
    interface-{method}-{name}.md
  inventory/module-map.json

**验证**: python <skill>/scripts/repo_knowledge.py doctor --repo <repo> --strict

> 完整文档见 references/FULL.md
```

完整原 SKILL.md 保存在 `references/FULL.md`。注意改造后版本比纯 Gene 多了 ~150 tokens 的目录规范和前后端做法说明——这是因为 v2 实验发现纯 Gene 会丢失 module-map.json 等关键结构约定。

---

## 四、为什么 GENE.md 不能单独作为文件被 agent 读取

当前主流 agent 框架的 skill 加载逻辑：

| 框架 | Skill 加载方式 | 会读 GENE.md 吗？ |
|------|---------------|:--:|
| **Claude Code** | 调用 Skill 工具 → 加载 `SKILL.md` → 作为系统指令注入 | ❌ 不会 |
| **Cursor** | 加载 `.cursor/skills/<name>/SKILL.md` | ❌ 不会 |
| **OpenCode** | 加载 skill 目录下的 `SKILL.md` | ❌ 不会 |
| **Copilot** | 通过自定义指令文件注入 | ❌ 不会 |

所有框架的约定都是**读 SKILL.md**。加一个 GENE.md 文件，框架不认识，不会自动加载。

要让框架读 GENE.md，需要：
- 改 Claude Code 的 skill 加载逻辑 → 需要 Anthropic 改代码
- 改 Cursor 的 skill 加载逻辑 → 需要 Cursor 团队改代码
- 每个框架各自适配 → 推广成本极高

**所以回到核心结论：利用现有约定，把 Gene 写成 SKILL.md 的全部内容，把详细文档移到 references/。**

---

## 五、实践指南

### 5.1 改造步骤

```
第 1 步: cp SKILL.md references/FULL.md          # 备份完整文档
第 2 步: 提取策略步骤 + AVOID + 结构规范，重写 SKILL.md  # 控制在 ~500 tokens
第 3 步: 在 SKILL.md 末尾引用 FULL.md              # "完整文档见 references/FULL.md"
第 4 步: git commit                                # 完成
```

### 5.2 改造后的目录结构

```
campus-repo-knowledge/
├── SKILL.md              ← 混合方案 (~450 tokens)，模型每次推理时注入
├── USAGE.md              ← 使用说明（给人看的快速入门）
├── GENE.md               ← Gene 参考副本（方便单独查阅和 diff 对比）
├── references/
│   ├── FULL.md           ← 原 SKILL.md 完整版（人类学习时看）
│   ├── archive-schema.md
│   ├── module-research.md
│   ├── writing-guide.md
│   ├── language-hints.md
│   └── subagent-workflow.md
├── scripts/
└── tests/
```

### 5.3 人类 vs 模型的阅读路径

```
模型调用 skill 时:
  加载 SKILL.md (~450 tokens 混合方案) → 执行任务
  需要参考时 → 模型会自己去 references/ 找对应文件

人类学习 skill 时:
  读 USAGE.md（快速入门）
  → 读 references/FULL.md（完整文档）
  → 读 references/ 下的各参考文件
  → 看 GENE.md（了解模型看到的控制指令）
```

### 5.4 什么场景适合这样改造

| ✅ 适合 | ❌ 可能不适合 |
|--------|------------|
| 有明确步骤的操作性 Skill | 纯知识库类 Skill（内容即价值） |
| 高频调用（节省的 token 累积显著） | 一次性 Skill |
| 有已知反模式/常见错误 | 探索性/创意性任务 |
| 需要场景路由的复杂 Skill | Skill 本身就 < 500 tokens |

---

## 六、我们的 A/B 实验 (v2 — 正确对照)

用 campus-repo-knowledge 初始化一个 Campus HR System 仓库。三个条件用完全相同的 Agent 调用方式，仅注入内容不同：

| 维度 | Baseline (无指导) | Before (完整 SKILL.md, 3,153 tokens) | After (纯 Gene, 280 tokens) |
|------|:--:|:--:|:--:|
| 每次注入 token | 0 | 3,153 | **280** |
| 模块归并 | ❌ 技术层 `common` 模块 | ✅ 纯业务，无技术层 | ✅ 纯业务（公共基础设施可接受） |
| 结构规范 | ❌ 无 module-map.json | ✅ module-map.json + 严格三层结构 | ⚠️ 扁平结构，无 module-map.json |
| 文档命名 | controller/service 技术后缀 | 规范 `interface-{method}-{name}` | 中文动词（入职/调动/离职） |
| 产出文件数 | 12 | 12 | 12 |
| 占位词残留 | 0 | 0 | 0 |
| 业务规则覆盖 | ✅ | ✅ | ✅ |

**关键发现**:
1. **纯 Gene (280 tokens) 丢失了结构规范**：没有 module-map.json，没有 `systems/modules` 三层目录。Gene 的 compact 性质必然丢失一些细节。
2. **完整 Skill (3,153 tokens) 结构最好但太费 token**：每次调用注入 3,153 tokens 不划算。
3. **最佳方案是混合**：SKILL.md = Gene (~300 tokens) + 结构规范 (~150 tokens) = **~450 tokens**。既保留了控制信号，又不丢失关键结构。

## 七、campus-repo-knowledge 的实际改造

基于实验结论，我们将 SKILL.md 改为混合方案：

```
改造前: SKILL.md = 3,153 tokens（全部文档）
改造后: SKILL.md = ~450 tokens（Gene + 结构规范）
         references/FULL.md = 3,153 tokens（人类深入学习时看）
```

**效果**: 模型每次调用 skill 时只注入 ~450 tokens（省 86%），同时保留 module-map.json 目录规范等关键结构信息。

---

## 八、总结

| 问题 | 答案 |
|------|------|
| Gene 是什么？ | 紧凑的结构化控制指令，包含触发词、策略步骤、AVOID 和验证方式 |
| 怎么让 agent 读到它？ | **把它写成 SKILL.md 的内容**（~450 tokens 混合方案）。原完整文档移到 references/FULL.md |
| 纯 Gene 够吗？ | 实验证明不够——会丢失结构规范。推荐混合方案：Gene + 关键结构规范 (~450-500 tokens) |
| 和 Skill 的关系？ | Gene 是 Skill 的模型接口。Skill 是完整知识包（FULL.md + references + scripts） |
| 为什么不单独建 GENE.md？ | 所有 agent 框架只读 SKILL.md。不加新文件类型，不依赖新协议 |
| 改造需要改 agent 架构吗？ | 不需要。利用现有约定：agent 读 SKILL.md → SKILL.md 变短即可 |
| 会丢失文档吗？ | 不会。完整文档在 references/FULL.md，人类随时可读 |

---

*参考论文: Wang, Ren, Zhang. From Procedural Skills to Strategy Genes (arXiv:2604.15097, 2026)*
*实验数据: `docs/experiments/results/experiment_evaluation.md`*
