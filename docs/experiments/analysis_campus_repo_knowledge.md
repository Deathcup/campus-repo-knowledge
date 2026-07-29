# campus-repo-knowledge 改造历程

本文档记录了将 campus-repo-knowledge 从传统 Skill 改造为 Gene 增强版的全过程，包括失败尝试和最终方案。

## 一、出发点

campus-repo-knowledge 是一个生产级的代码仓知识库生成 Skill。改造前的 SKILL.md 为 3,153 tokens，加上 references/ 和 scripts/ 后整个 Skill 包约 33,000 tokens。

根据论文 (arXiv:2604.15097) 的发现：超过 2,500 tokens 的文档型 Skill 会导致控制信号稀释，甚至拖慢强模型性能（-9.4pp）。这促使我们探索改造方案。

## 二、v1 尝试（失败）

最初的理解是：Gene 是 Skill 的增强，作为独立 section 插入 SKILL.md 开头。

```
v1 方案: SKILL.md = Gene section (~280 tokens) + 原有完整正文 (~3,000 tokens)
```

**失败原因**: 模型仍然会读完整个 SKILL.md（3,280 tokens），控制信号照样被稀释。Gene section 只是增加了更多 token，没有解决核心问题。

## 三、v2 实验（找到正确方案）

重新设计了 3 条件对照实验：

| 条件 | SKILL.md 内容 | Token 数 | 结果 |
|------|-------------|---------|------|
| Baseline | 无 Skill | 0 | 生成技术层模块（common），命名用 controller/service 后缀 |
| Before | 完整原始 SKILL.md | 3,153 | ✅ 结构规范完美，❌ 每次推理太贵 |
| After | 纯 Gene | 280 | ✅ 业务命名好，❌ 丢了 module-map.json 和目录规范 |

**关键发现**: 纯 Gene 太简（丢结构），纯 Skill 太贵（3,153 tokens）。最优解是**取中间**。

## 四、最终方案：混合

```
SKILL.md (~450 tokens):
  ├── Gene 控制指令 (场景路由、策略步骤、AVOID)
  └── 关键结构规范 (目录格式、命名约定、验证方式)

references/FULL.md (3,153 tokens):
  └── 原完整 SKILL.md，人类深入学习时阅读
```

**效果**:
- 每次推理注入: 3,153 → ~450 tokens（省 86%）
- 结构规范: ✅ 保留 module-map.json 目录约定
- 控制信号: ✅ AVOID 信号在模型读取的最前位置
- Agent 框架: 无需任何改动，照常读 SKILL.md

## 五、SKILL.md 改造对比

### 改造前 (3,153 tokens)

```
---
name: campus-repo-knowledge
description: 为代码仓生成、查询和维护...（150 字长描述）
---

# Campus Repo Knowledge

## 不可妥协的结果
9 条铁律，散文式描述 (~500 tokens)

## 任务路由
6 种场景 (~200 tokens)

## 分层查询
6 步详细流程 (~400 tokens)

## 初始化/升级
17 步详细操作 (~900 tokens)

## 增量需求 (...)
## 完成后归档 (...)
## 未知改动同步 (...)
## 内部命令 (API 参考)
## 按需读取参考
```

### 改造后 (~450 tokens)

```
---
name: campus-repo-knowledge
description: 在目标仓库建立和维护分层中文知识库。详细文档见 references/FULL.md
---

## 策略基因

**触发词**: ...
**场景路由**: 4 种场景，3 行
**初始化要点**: 5 步核心流程
**怎么做（后端/前端）**: 各 2-3 条原则
**不要做**: 6 条 AVOID
**目录规范**: 树形结构展示
**验证**: doctor --strict

> 完整文档见 references/FULL.md
```

### 核心改造原则

1. **删**: 概述、背景说明、教学性解释、代码示例、排错指南 → 移入 references/FULL.md
2. **留**: 场景路由、策略步骤、AVOID、目录规范、验证命令
3. **改**: 散文描述 → 结构化条目；长段落 → 短列表
4. **不加**: 不增加新文件类型，不依赖新协议，框架零改动

## 六、适用范围

这种改造方式适合：
- 有明确操作步骤的 Skill（策略步骤可枚举）
- 有已知反模式/常见错误的 Skill（AVOID 价值高）
- 高频调用（节省的 token 累积明显）
- SKILL.md 超过 1,000 tokens（信号稀释风险高）

不太适合：
- 纯知识库类 Skill（内容本身即价值，无法压缩）
- SKILL.md 本身就 < 500 tokens（已经够紧凑）

---

*改造日期: 2026-07-29*
*基于论文: Wang, Ren, Zhang. From Procedural Skills to Strategy Genes (arXiv:2604.15097)*
