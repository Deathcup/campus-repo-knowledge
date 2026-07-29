# 什么是 Gene？

Gene 是 Skill 的一种优化写法——把 SKILL.md 从一本"操作手册"变成一张"执行卡片"，用更少的 token 让模型表现更好。

## 问题在哪

一个典型的 SKILL.md 长这样：概述、工作流、代码示例、API 参考、排错指南……洋洋洒洒两三千字。Agent 框架调用 skill 时，会把整个文件塞进模型上下文。

论文 (arXiv:2604.15097) 做了 4,590 次实验，结论很直白：**文档越长，模型越容易走偏。** 完整 Skill 包让 Gemini Pro 的性能从 60.1% 掉到 50.7%。但把同样的经验浓缩成 230 tokens 的结构化指令后，性能反而涨了 3 个百分点。

问题不在内容，在形式。文档是写给人看的，模型需要的是指令。

## 怎么解决

所有 agent 框架都只认 `SKILL.md`。那就利用这个约定——**把 SKILL.md 写短**，详细文档丢到 `references/` 里。

```
改造前:                              改造后:
├── SKILL.md    ← 3,153 tokens       ├── SKILL.md    ← ~450 tokens
│   (每次全量注入，信号被稀释)          │   (紧凑指令，信号集中)
└── references/                      ├── references/
    ├── archive-schema.md            │   ├── FULL.md  ← 原完整版，人看
    ├── ...                          │   ├── ...
```

Agent 照常加载 SKILL.md，不需要改一行框架代码。只是内容从 3,000 字变成了 400 字。

## Gene 到底长什么样

就是 SKILL.md 最开头的一个 section，用固定格式写清楚：触发时机、怎么做、别做什么、怎么检查。

```markdown
## 策略基因

**触发词**: repo-knowledge, .repo-knowledge, 知识库

**场景路由**:
- 目录不存在 → 初始化
- 用户问代码 → 分层查询
- 开发完成 → 归档

**怎么做**:
1. 先用 init 脚本扫仓库
2. 编辑 module-map.json，把 Controller/Service 等技术名归并成业务模块
3. 每个模块至少 3 份文档，后端按接口拆，前端按页面拆

**不要做**:
- 别把 Controller/Service/Mapper 当模块名
- 别把所有东西塞进一个 overview.md
- 别跳过渐进查询直接全局搜索
- 别留 "待补充"/"TODO" 这种占位词

**目录规范**: .repo-knowledge/INDEX.md → systems/<子系统>/ → modules/<模块>/
**验证**: doctor --strict
```

## 和直接把 Skill 写短的区别

不是简单压缩。有三件事不太一样：

1. **删什么**：概述、背景介绍、代码示例、API 参数表——这些给人看，模型不需要。
2. **留什么**：策略步骤、场景路由、触发词、验证命令。
3. **加什么**：AVOID 信号。论文发现"告诉模型别做什么"比"告诉它要做什么"有效近一倍（+4.6 vs +2.5pp）。这些在原 Skill 里往往根本没有。

## 为什么不能单独建个 GENE.md

因为所有框架都只读 SKILL.md。Claude Code、Cursor、OpenCode——没一个会主动加载 GENE.md。想让它们读，得挨个改框架代码，不现实。把内容写在 SKILL.md 里，什么也不用改。

## 怎么改

四步：

1. `cp SKILL.md references/FULL.md` —— 备份
2. 从原文里提取策略步骤和场景路由，从失败经验里提炼 AVOID
3. 加上必要的目录约定和验证命令，控制在 500 tokens 内
4. 末尾加一行 `> 完整文档见 references/FULL.md`

## 我们的实验

用 campus-repo-knowledge 初始化一个真实的 Spring Boot 仓库，对比三种情况：

| | 无 Skill | 完整 SKILL.md (3,153 tokens) | 混合方案 (~450 tokens) |
|------|:--:|:--:|:--:|
| 模块归并 | ❌ 建了技术层 common 模块 | ✅ | ✅ |
| 结构规范 (module-map.json) | ❌ | ✅ | ✅ |
| 命名风格 | controller/service 技术后缀 | interface-{method}-{name} | 中文业务名 |
| 占位词 | 0 | 0 | 0 |

**纯 Gene (280 tokens) 丢东西了**——没有 module-map.json，目录结构也不对。太短也不行。加回 ~150 tokens 的结构规范后就刚好。

## 适合什么场景

**适合**: 步骤明确、高频调用、有已知坑位的 Skill。改一次省几十万 token。
**不适合**: 纯知识库（内容本身就是价值）、本来就很短的 Skill (< 500 tokens)、一次性任务。

## 一句话总结

> 把 SKILL.md 从操作手册变成执行卡片——写清楚做什么、怎么做、别做什么。控制在 500 字以内。完整文档丢 references/。不用改任何框架。

---

*论文: Wang, Ren, Zhang. From Procedural Skills to Strategy Genes (arXiv:2604.15097, 2026)*
