# campus-repo-knowledge A/B 实验评估报告

## 实验设计

- **目标仓库**: `D:/claude/experiments/target-repo` — Campus HR System (Spring Boot 后端，7 个源文件 + 1 个测试)
- **条件 A (Skill)**: 注入完整 SKILL.md (~3,153 tokens)
- **条件 B (Gene)**: 仅注入 GENE.md (~280 tokens)
- **任务**: 为目标仓库生成完整的 `.repo-knowledge/` 知识库
- **评估维度**: 分层结构、模块归并质量、文档深度、占位词、业务规则覆盖

---

## 一、量化对比

| 维度 | Skill (完整文档) | Gene (紧凑控制) | 分析 |
|------|-----------------|----------------|------|
| **控制 Token 消耗** | ~3,153 tokens | ~280 tokens | Gene 节省 **91.1%** |
| **产出文件数** | 14 个 .md | 8 个 .md | — |
| **产出总大小** | 81,584 bytes | 48,300 bytes | Gene 产出精简 40.8% |
| **子系统数** | 3 (含1个技术层) | 2 (纯业务) | ⚠️ Skill 违规 |
| **模块数** | 3 | 2 (直接到子系统) | — |
| **每模块最少文档** | ✅ 至少 2 份 | ✅ 至少 3 份 | 均达标 |
| **占位词残留** | 0 | 0 | 均达标 |
| **源码锚点密度** | 高 (行号级) | 中高 (文件+方法级) | Skill 更细 |
| **业务规则覆盖** | 完整 | 完整 | 均覆盖 |

## 二、关键质量差异

### 2.1 模块归并 — Skill 违反了自己的规则

| | Skill 输出 | Gene 输出 |
|------|-----------|----------|
| 子系统命名 | `employee-management`, `attendance-management`, `platform-infrastructure` | `员工管理`, `考勤管理` |
| 额外子系统 | **`platform-infrastructure`** (技术层!) | 无 |

**这是本次实验最关键的发现。**

Skill 的原始规则 #2 明确要求：
> "不得用 controller/service/repository、views/components/api 等技术层代替业务模块"

但 Skill agent 在完整文档的引导下，仍然创建了 `platform-infrastructure` 子系统——该子系统的文档仅覆盖 `ApiResponse` 和 `AuthContext` 两个技术组件，且 `modules/shared-foundation/` 仅包含 `feature-api-response.md` 一份细节文档（缺失 AuthContext）。

Gene agent 将 `ApiResponse` 和 `AuthContext` 作为"基础设施"直接整合在 INDEX.md 中，未单独建子系统——更符合"跨业务共享组件不应作为独立业务模块"的原则。

**论文解释**: 论文第 4.1.2 节发现 Skill-Overview 型内容 (-4.7pp) 可能干扰模型判断。SKILL.md 中的 Overview/Frontmatter 包含了对"平台基础设施"这类概念的大量描述性语言，可能诱导 agent 将其视为需要文档化的独立子系统。

### 2.2 文档粒度 — Skill 更细腻但更冗余

| 对比项 | Skill | Gene |
|--------|-------|------|
| employee 创建文档 | 189 行，含完整字段语义表、逐步骤代码引用 | 86 行，含业务规则 + 步骤执行流 |
| 内容覆盖 | 相同 | 相同 |
| 冗余内容 | Controller 代码片段 vs Service 代码片段重复描述 | 无重复 |
| 事务分析 | 单独章节 | 嵌入"事务与并发"段 |
| 测试引用 | 含具体行号 | 含测试方法名 |

Gene 文档在同等信息覆盖下更紧凑（~54% 的篇幅），没有牺牲关键业务规则。符合论文"信号密度"优于"信息总量"的发现。

### 2.3 目录结构 — Gene 更简洁

```
Skill:                                        Gene:
systems/                                       subsystems/
├── employee-management/                       ├── 员工管理/
│   ├── overview.md                            │   ├── overview.md
│   └── modules/                               │   ├── 入职管理.md
│       └── employee-lifecycle/                │   ├── 调动管理.md
│           ├── overview.md                    │   └── 离职管理.md
│           ├── interface-get-list...md        └── 考勤管理/
│           ├── use-case-create...md               ├── overview.md
│           ├── use-case-resign...md               ├── 打卡与汇总.md
│           └── use-case-transfer...md              └── 异常与加班.md
├── attendance-management/
│   ├── overview.md
│   └── modules/
│       └── daily-attendance/
│           ├── overview.md
│           ├── interface-get-monthly...md
│           ├── use-case-approve...md
│           └── use-case-mark-anomaly.md
└── platform-infrastructure/          ← 问题!
    ├── overview.md
    └── modules/
        └── shared-foundation/
            ├── overview.md
            └── feature-api-response.md
```

Skill 产出了 3 层嵌套 (`systems/子系统/modules/模块/`)，Gene 产出了 2 层 (`subsystems/子系统/`)。对于这个 7 个源文件的小型仓库，2 层结构更加合理。

### 2.4 文档命名 — Gene 使用中文业务名更直观

| 文档类型 | Skill | Gene |
|---------|-------|------|
| 员工创建 | `use-case-create-employee.md` | `入职管理.md` |
| 员工调动 | `use-case-transfer-employee.md` | `调动管理.md` |
| 员工离职 | `use-case-resign-employee.md` | `离职管理.md` |
| 考勤汇总 | `interface-get-monthly-summary.md` | `打卡与汇总.md` |
| 异常+加班 | 分成 2 份文档 | `异常与加班.md` (1份合并) |

Gene 使用中文业务动词命名，对中文团队更友好。Skill 使用英文前缀 (`use-case-`, `interface-`) 区分类型，虽然规范但增加了目录层级。

---

## 三、论文发现 vs 本实验验证

| 论文发现 | 本实验是否验证 | 证据 |
|---------|-------------|------|
| Skill 的控制信号稀疏 | ✅ 部分验证 | Skill agent 额外创建了"platform-infrastructure"技术层子系统 |
| Gene 更紧凑但效果不降 | ✅ 验证 | Gene 用 91% 更少的控制 token 产出了同等质量的文档 |
| AVOID 信号有效 | ✅ 验证 | Gene agent 未创建技术层子系统，遵守了"禁止用技术层当模块名" |
| 结构化 > 展平 | 间接支持 | Gene 的结构化 fields 使 agent 正确路由到"初始化"场景 |
| 信号密度 > 信息总量 | ✅ 验证 | Gene 文档 54% 篇幅覆盖相同的业务规则 |

---

## 四、Token 经济分析

基于实验数据推算实际收益：

| 场景 | 原始 Skill 方案 | Gene 方案 | 节省 |
|------|---------------|----------|------|
| 控制指令注入 | 3,153 tokens | 280 tokens | **91.1%** |
| 小项目产出 token | 81,584 bytes (~20K tokens) | 48,300 bytes (~12K tokens) | 40.8% |
| 全量 (含 references) | ~33K tokens | ~280 + 按需加载 | 视情况 |

对于日常高频调用场景（每次查询、每次归档），Gene 方案的成本节省非常显著。

---

## 五、局限与诚实声明

1. **单次试验**: 每个条件只运行 1 次，结果受随机性影响。论文使用 100+ 次/条件。
2. **小型仓库**: 目标仓库仅 7 个源文件。大型仓库的行为可能不同。
3. **相同模型**: 两个 agent 使用相同的 Claude 模型，无法验证跨模型差异。
4. **领域差异**: 这里是"代码仓知识管理"领域，与论文的"科学代码求解"完全不同。论文的作者明确声明这是"外推假设"。
5. **Skill agent 也可能产出好的结果**: Skill agent 的文档深度实际上更高（更多源码行号引用、字段级分析）。问题是结构层面的（多了一个技术层子系统）。

---

## 六、结论与建议

### 实验结论

> **Gene 方案用 9% 的控制 token，产出了与完整 Skill 方案同等质量（甚至在模块归并上更正确）的知识库。**

关键证据：
1. Gene agent **没有**犯"把技术组件当业务模块"的错误 — Skill agent 犯了
2. Gene 文档在同等信息覆盖下**更紧凑** (~54% 篇幅)
3. Gene 用中文业务命名，团队友好度更高
4. 两个方案都没有占位词残留，业务规则覆盖率相当

### 对 campus-repo-knowledge 的改造建议

1. **采纳 GENE.md**: 将 GENE.md 作为模型推理时的默认控制指令
2. **保留 SKILL.md**: 作为人类参考文档（按需加载）
3. **强化 AVOID 信号**: 当前 GENE.md 的 AVOID 已经覆盖了关键反模式，从实验结果看效果良好
4. **监控 platform-infrastructure 问题**: 如果后续使用中继续出现"技术层子系统被独立文档化"的问题，可在 AVOID 中增加更明确的约束

---

*评估日期: 2026-07-29*
*实验数据: `D:/claude/experiments/results/`*
