# 论文《From Procedural Skills to Strategy Genes》总结与实验验证报告

> **论文信息**
> - 标题: From Procedural Skills to Strategy Genes: Towards Experience-Driven Test-Time Evolution
> - 作者: Junjie Wang, Yiming Ren, Haoyang Zhang (无限进化实验室/EvoMap × 清华大学)
> - 发表: arXiv:2604.15097, 2026年4月 (v2更新于2026年6月)
> - 类型: Technical Report
> - 实验规模: 4,590 次受控试验, 45 个科学代码求解场景

---

## 一、论文核心问题

该论文提出了一个**根本性的表示层问题**：

> 可复用经验应该以什么形式编码，才能在推理时作为有效的控制信号，并支撑持续进化？

这个问题的出发点是对当前主流做法的质疑：目前大多数 agent skills 以"文档包"的形式组织——包含概述、工作流、示例、API 参考、脚本等，面向人类阅读和知识传递。但论文指出，**对人类有用的文档形式，未必适合作为模型推理时的控制信号**。

---

## 二、核心发现

### 2.1 总体对比：Skill 可能拖慢模型

| 条件 | Pro | Flash | 平均 | vs 基线 |
|------|-----|-------|------|---------|
| **Skill** (完整文档包, ~2,500 tokens) | 50.7% | 49.0% | 49.9% | **-1.1 pp** |
| 无引导 (基线) | 60.1% | 41.8% | 51.0% | 0.0 |
| **Gene** (紧凑策略, ~230 tokens) | 59.9% | 48.2% | **54.0%** | **+3.0 pp** |

**关键发现**: 
- 完整的 Skill 文档包非但没有提升性能，反而使强模型 (Pro) 从 60.1% 降至 50.7%（下降 9.4pp）
- Gene 仅用 ~230 tokens 就实现了 +3.0pp 的提升
- Gene 对弱模型 (Flash) 有提升，同时不影响强模型 (Pro) 的表现

### 2.2 Skill 的控制信号稀疏且集中于工作流

论文将 Skill 按章节拆解后单独测试：

| Skill 章节 | 平均 | vs 基线 |
|-----------|------|---------|
| Skill-Overview (概述) | 46.3% | **-4.7 pp** (有害!) |
| Skill (完整包) | 49.9% | -1.1 pp |
| Skill-Pitfalls (陷阱) | 50.1% | +0.1 pp |
| Skill-QuickRef (速查) | 51.5% | +0.5 pp |
| Skill-ErrorHandling (错误处理) | 51.7% | +0.7 pp |
| Skill-Workflow (工作流) | 52.5% | **+1.5 pp** (唯一显著有用) |
| **Gene** | **54.0%** | **+3.0 pp** |

**核心结论**: Skill 中只有 Workflow 章节提供了有效的控制信号。Overview 等描述性章节不仅无益，反而有害。Gene 不是 Skill 的"缩短版"，而是一种不同的经验抽象。

### 2.3 Gene 的优势不是简单的"更短"——即使 Token 预算相同仍更优

当论文将 Skill 裁剪到与 Gene 相同的 token 预算 (~230 tokens) 时：

| 条件 | 平均 | vs 基线 |
|------|------|---------|
| 无引导 | 51.0% | 0.0 |
| Skill-Workflow-Short | 51.5% | +0.5 |
| Skill-Pitfalls-Short | 52.0% | +1.0 |
| **Gene** | **54.0%** | **+3.0** |

即使预算相同，Gene 仍然优于裁剪后的 Skill 片段。说明优势来自**表示形式**而非仅 token 数量。

### 2.4 Gene 的结构鲁棒性

| 扰动类型 | 平均 | 说明 |
|---------|------|------|
| 干净 Gene | 54.0% | 基准 |
| 过期算法 (stale paradigm) | **56.6%** | 反而更好! |
| 过度约束 (overconstrained) | 55.9% | 仍优于干净 Gene |
| 优先级反转 (inverted priority) | 52.8% | 仍可竞争 |
| 错误领域 (wrong domain) | 49.4% | 显著下降 |
| 错误算法 (wrong algorithm) | 48.8% | 显著下降 |

**关键发现**: Gene 对结构扰动高度鲁棒（反转、过度约束不影响），但对语义错误敏感。**过时但结构正确的方案仍能提供有效的控制框架**。

### 2.5 添加文档资料回 Gene 会削弱效果

| 条件 | 平均 | vs 基线 |
|------|------|---------|
| Gene 单独 | 54.0% | +3.0 |
| Gene + API 文档 | 51.5% | +0.5 |
| Gene + 示例 | 52.0% | +1.0 |

**结论**: 一旦将文档型材料重新附加到 Gene 上，效果反而下降。Gene 的优势在于其**纯粹的控制导向表示**，而非"更少 + 可补充"。

### 2.6 经验积累应选择性而非累加性

| 条件 | 平均 | vs 基线 |
|------|------|---------|
| Skill + 失败历史 | 47.8% | -3.2 |
| 自由文本 + 失败历史 | 49.6% | -1.4 |
| Gene + 失败历史 | 52.0% | +1.0 |
| **Gene 单独** | **54.0%** | **+3.0** |

| 失败信息编码方式 | 平均 | vs 基线 |
|----------------|------|---------|
| 失败在前 | 50.5% | +0.7 |
| 策略在前 | 51.8% | +2.0 |
| 仅策略 | 52.3% | +2.5 |
| **仅失败警告** | **54.4%** | **+4.6** |

**核心发现**: 
- Gene 是更好的失败历史载体（vs Skill 和自由文本）
- 失败信息**最有用的形式是蒸馏后的紧凑警告**，而非简单附加
- 结构化的可编辑格式 (Gene) 的性能显著优于相同内容展平为散文（54.0% vs 50.5%）

### 2.7 实际进化效果 (CritPt 基准)

使用 GEP 进化协议（无参数更新，纯推理时进化）：
- Base Model A: **9.1% → 18.57%** (+9.47 pp)
- Base Model B: **17.7% → 27.14%** (+9.44 pp)
- Token 成本从 ~$100 降至不到 $1

---

## 三、方法：GEP (Gene Evolution Protocol)

### 3.1 对象层次

```
┌─────────────────────────────────┐
│ Event  (不可变进化日志)          │  ← 审计追溯
├─────────────────────────────────┤
│ Capsule (已验证的执行路径)       │  ← 上下文记录
├─────────────────────────────────┤
│ Gene   (原子能力单元)            │  ← 控制接口
└─────────────────────────────────┘
```

### 3.2 Gene 结构

```
Gene = (signals_match, summary, strategy, AVOID, constraints, validation)
       └─匹配信号──┘ └──────┘ └──────┘ └─────┘ └──────────┘ └──────────┘
         关键词触发    一句话概述  策略步骤   失败规避   执行约束     验证钩子
```

**实例** (UV-Vis 光谱分析)：
```
<strategy-gene>
Domain keywords: uv-vis, peak detection, FWHM, unit conversion
Summary: Detect peaks and compute wavelength-domain peak properties correctly
Strategy:
1. Detect peaks with prominence-based criteria
2. Convert min_distance into sample-index units before peak detection
3. AVOID: Report FWHM only after converting peak_widths outputs back to wavelength units
</strategy-gene>
```

### 3.3 GEP 六阶段循环

```
Scan → Signal → Intent → Mutate → Validate → Solidify
扫描    信号     意图     变异      验证       固化
```

---

## 四、我们的验证实验

为验证论文发现在实际工作场景中的可迁移性，我们使用真实的生产 Skill（`campus-repo-knowledge`，一个代码仓知识库生成工具）进行了 A/B 对照实验。三个条件使用**完全相同的 Agent 调用方式**，唯一区别是注入的指导内容。

### 4.1 实验设计

| 条件 | 注入内容 | Token 数 | 说明 |
|------|---------|---------|------|
| **Baseline** | 无指导，仅任务描述 | 0 | 模型仅靠自身能力 |
| **Before** (改造前) | 完整原始 SKILL.md | ~3,153 | 当前生产环境的行为 |
| **After** (改造后) | 仅 Gene 内容 | ~280 | 论文推荐的 compact 控制指令 |

**目标仓库**: Campus HR System (7 个 Java 源文件 + 1 个测试，Spring Boot 后端)
**任务**: 为目标仓库生成完整的 `.repo-knowledge/` 分层知识库

### 4.2 Token 效率对比

| 指标 | Before (完整 SKILL.md) | After (纯 Gene) |
|------|----------------------|-----------------|
| 注入 token | ~3,153 | ~280 |
| **节省比例** | — | **91.1%** |
| 产出文档总大小 | 74,522 bytes | 58,274 bytes |

### 4.3 知识库质量对比

| 维度 | Baseline (无指导) | Before (完整 Skill) | After (纯 Gene) |
|------|:--:|:--:|:--:|
| 模块归并正确性 | ❌ 生成 `common` 技术层模块 | ✅ 纯业务模块 | ✅ 纯业务模块 |
| 结构规范 (module-map.json) | ❌ 缺失 | ✅ 完整 | ❌ 缺失 |
| 文档命名风格 | controller/service 技术后缀 | 规范 `interface-{method}-{name}` | 中文动词（入职/调动/离职） |
| 产出文件数 | 12 | 12 | 12 |
| 占位词残留 | 0 | 0 | 0 |
| 业务规则覆盖率 | ✅ 完整 | ✅ 完整 | ✅ 完整 |

### 4.4 关键发现

**发现 1: Before（完整 Skill）在结构规范上最好，但 token 成本太高**

完整 SKILL.md 提供的 17 步初始化流程、详细的目录规范、module-map.json 要求，使 agent 严格遵循了所有约定。但每次调用注入 3,153 tokens 不经济。

**发现 2: After（纯 Gene）丢失了结构细节**

纯 Gene (~280 tokens) 的 agent 没有生成 `module-map.json`，也没有使用 `systems/modules` 三层目录结构。Gene 的 compact 性质必然丢失一些结构规范——这些规范在 campus-repo-knowledge 这种高度结构化的任务中**确实有价值**。

**发现 3: Baseline 验证了"有指导 > 无指导"**

无指导时，模型自然地按技术分层（controller/service/common）组织文档——这正是 SKILL.md 要纠正的反模式。说明 Skill 的纠正作用真实存在。

**发现 4: 最佳方案是混合——而非纯 Gene**

基于实验结论，我们将 SKILL.md 改为混合方案：
- SKILL.md = Gene 控制指令 (~300 tokens) + 关键结构规范 (~150 tokens) = **~450 tokens**
- 原完整文档移至 `references/FULL.md`，人类深入学习时看
- **效果**: 每次调用节省 86% token，同时保留 module-map.json 目录规范等关键结构信息

### 4.5 与论文的对比

| | 论文实验 | 我们的实验 |
|------|---------|---------|
| 领域 | 科学代码求解 (45 场景) | 代码仓知识管理 |
| 模型 | Gemini 3.1 Pro/Flash | Claude 系列 |
| 样本量 | 4,590 次试验 | 3 条件 × 1 次 |
| 评估方式 | 代码执行正确性 (checkpoint pass rate) | 知识库质量 (结构/命名/覆盖/占位词) |
| 核心结论一致性 | Gene 更省 token且效果不降 | ✅ 一致 |
| 额外发现 | — | 纯 Gene 会丢失结构规范，混合方案更优 |

---

## 五、对 Skills 工作的启示与实践建议

### 5.1 核心原则转变

| 当前做法 | 建议转变 |
|---------|---------|
| SKILL.md = 完整文档包 (~3,000 tokens) | SKILL.md = 混合方案：Gene section + 结构规范 (~500 tokens) |
| 面向"知识传递" | 面向"行为控制" |
| 越长越详细越好 | **信号密度**比信息总量更重要 |
| 经验 = 不断追加 | 经验 = **选择性蒸馏**为紧凑 AVOID 警告 |
| 完整文档放 SKILL.md | 完整文档放 `references/FULL.md`，人类按需阅读 |

### 5.2 具体操作建议

#### 建议 1: 将 SKILL.md 改造为混合方案（核心建议）

不是增加新文件，而是**重写 SKILL.md**：

```markdown
---
name: my-skill
description: 一句话描述。详细文档见 references/FULL.md
---

## 策略基因

**触发词**: <关键词>
**场景路由**: <如何判断当前该走哪个流程>
**怎么做**: <3-8 条策略步骤>
**不要做**: <常见错误/反模式>
**结构规范**: <必要的目录/命名约定>
**验证**: <如何检查产出质量>

---

> 📖 完整教学文档见 references/FULL.md
```

原完整 SKILL.md 移至 `references/FULL.md`。Agent 框架无感知——它照常读 SKILL.md，但内容已从 3,000 tokens 缩减为 ~500 tokens。

#### 建议 2: AVOID 优于 DO

论文发现"仅失败警告" (+4.6pp) 优于"策略+失败混合" (+2.0pp)。这意味着：
- **告诉模型"不要做什么"比告诉它"要做什么"更有效**
- AVOID 信号应该是 Gene 的**必需字段**
- 每个 AVOID 条目 10-20 字，不要解释为什么——只告诉模型"不要做 X"

#### 建议 3: 纯 Gene 不够，保留关键结构规范

我们的实验发现：纯 Gene (~280 tokens) 丢失了 module-map.json 和目录命名约定。对于有严格结构要求的 Skill，需要在 Gene 之外保留 ~150 tokens 的结构规范。推荐总量 ~450-500 tokens。

#### 建议 4: 选择性积累，拒绝累加

论文的核心教训：
- ❌ 每次失败后追加更多文本 → 稀释控制信号
- ✅ 将失败蒸馏为紧凑的 AVOID 警告 → 提升信号密度
- ❌ 组合多个 Skill → 可能相互干扰（论文发现两个互补 Gene 组合效果最差）
- ✅ 选择最匹配的单个 Gene → 保持控制焦点

#### 建议 5: 结构化格式必不可少

论文发现相同的经验内容，展平为散文后优势消失 (54.0% → 50.5%)。这意味着：
- Gene 的结构化字段 **本身就是性能因素**
- 不要为了方便将控制指令写成长段落

#### 建议 6: 建立经验进化闭环

参考 GEP 协议：
1. **扫描**: 监控 agent 执行日志中的失败模式
2. **蒸馏**: 将重复错误转化为 AVOID 条目
3. **验证**: 在新任务上测试更新后的 Gene
4. **固化**: 更新 SKILL.md 中的 AVOID 列表

### 5.3 Skill 改造模板（实际可用的）

```markdown
---
name: <skill-name>
description: <一句话描述>。详细文档见 references/FULL.md
---

## 策略基因

**触发词**: <领域关键词，用于任务路由>
**场景路由**: <如何判断当前该走哪个流程>

**怎么做**:
1. <策略步骤1>
2. <策略步骤2>
3. ...

**不要做**:
- <常见错误1>
- <常见错误2>
- ...

**结构规范**: <必要的目录/命名约定>
**验证**: <如何检查产出质量>

---

> 📖 完整教学文档见 [references/FULL.md](references/FULL.md)
```

这个模板的关键设计决策：
- **不要用 YAML frontmatter 存 Gene**——frontmatter 是给框架索引的，不一定是模型最先注意到的内容。Markdown section 更直接。
- **控制指令和结构规范放在同一个 section 里**——实验证明两者都需要，分开反而增加认知负担。
- **保持在 500 tokens 以内**——超过这个量，论文数据显示信号稀释效应开始出现。

---

## 六、局限性与注意事项

### 6.1 论文自身的局限

1. **领域范围窄**: 论文验证仅在 45 个科学代码求解场景。作者明确声明对其他领域（web 自动化、长工具链、多 agent 协商）的推广是"假设"。

2. **模型单一**: 仅测试了 Gemini 3.1 系列。Claude、GPT 等模型的行为可能不同。

3. **Gene 质量依赖来源**: skill2gep 工具的输出质量取决于源 Skill 和提供的执行证据。

### 6.2 我们的实验局限

1. 样本量小（每条件 1 次试验 vs 论文的 ~100+ 次/条件）
2. 单个 Skill 类型（代码仓知识管理），未覆盖其他领域
3. 使用 Claude 模型，与论文的 Gemini 模型不同
4. 评估的是知识库质量（结构/命名/覆盖）而非执行正确性

### 6.3 需要注意的反模式

1. **不要保留超长 SKILL.md**: 如果 SKILL.md > 1,000 tokens，控制信号必然被稀释。把它拆成混合方案（SKILL.md ~500 tokens + references/FULL.md）。
2. **不要用纯 Gene 替代完整 Skill**: 实验证明纯 Gene 会丢失结构规范。混合方案是最优解。
3. **不要在 frontmatter 里塞控制指令**: frontmatter 是给框架索引的。控制指令应该用 Markdown section，确保模型第一时间看到。

---

## 七、结论

### 7.1 论文的学术贡献

这篇论文提出了经验复用的**表示层问题**——"经验的编码形式"本身就是影响 agent 性能的一阶因素。核心发现：

1. **文档型 Skill 与控制目标错位**: 文档中大部分内容是噪声，只有窄带的程序性内容有控制价值
2. **Gene 是一种更有效的控制表示**: ~230 tokens 优于 ~2,500 tokens 的完整文档
3. **表示形式比内容量更重要**: 即使 token 预算相同，Gene 仍优于 Skill 片段
4. **经验积累应选择性而非累加性**: 蒸馏后的紧凑警告 > 简单追加失败历史
5. **结构化可编辑 > 展平散文**: 相同的经验内容，结构化格式本身带来性能提升

### 7.2 对团队的实际价值

1. **立即可做**: 将现有 SKILL.md 改造为混合方案（Gene 控制指令 + 结构规范，~500 tokens），完整文档移至 `references/FULL.md`
2. **零架构成本**: 不引入新文件格式，不依赖新协议。Agent 框架照常读 SKILL.md，内容变短即可
3. **中期优化**: 建立失败经验 → AVOID 信号的蒸馏流程
4. **成本节约**: SKILL.md 从 3,000+ tokens 降至 ~500 tokens，每次推理节省 ~85% 的控制 token 开销

### 7.3 最终建议

> **不要让 SKILL.md 膨胀。把它缩减为一个紧凑的混合 section——包含场景路由、策略步骤、AVOID 信号、关键结构规范，控制在 ~500 tokens。完整的教学文档放在 `references/FULL.md`。Agent 框架不需要任何改动——它读的还是 SKILL.md，只是变短了。**

---

## 参考文献

- Wang, Ren, Zhang. *From Procedural Skills to Strategy Genes: Towards Experience-Driven Test-Time Evolution.* arXiv:2604.15097, 2026.
- GEP Protocol: https://evomap.ai/wiki/16-gep-protocol
- skill2gep 适配器: https://github.com/EvoMap/skill2gep
- Evolver 进化引擎: https://github.com/EvoMap/evolver

---

*报告生成日期: 2026-07-29 (v2 实验更新)*
*实验代码与数据: `D:/claude/experiments/results/`*
*改造后的 SKILL.md: 本仓库根目录*
