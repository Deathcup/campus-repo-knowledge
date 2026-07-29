# campus-repo-knowledge A/B 实验评估 (v2 — 正确对照)

## 实验设计

**三个条件使用完全相同的 Agent 调用方式**，唯一区别是注入的指导内容：

| 条件 | 注入内容 | Token 数 | 说明 |
|------|---------|---------|------|
| **Baseline** | 无指导，仅任务描述 | 0 | 模型只靠自身能力 |
| **Before** (改造前) | 完整原始 SKILL.md | ~3,153 | 当前生产环境的行为 |
| **After** (改造后) | 仅 Gene 内容 | ~280 | 论文推荐的 compact 控制指令 |

**目标仓库**: Campus HR System (7 个 Java 源文件 + 1 个测试)
**任务**: 为目标仓库生成完整的 `.repo-knowledge/` 知识库
**评估维度**: 模块归并正确性、文档质量、结构规范、token 效率、占位词

---

## 一、量化对比

| 维度 | Baseline | Before (完整 Skill) | After (仅 Gene) |
|------|:--:|:--:|:--:|
| **指导 token 消耗** | 0 | 3,153 | **280** |
| **产出文件数** | 12 | 11 | 12 |
| **产出总大小** | 74,915 bytes | 74,522 bytes | **58,274 bytes** |
| **占位词** | ✅ 0 | ✅ 0 | ✅ 0 |
| **module-map.json** | ❌ 缺失 | ✅ 已创建 | ❌ 缺失 |

## 二、模块归并分析（核心评估维度）

### Baseline (无指导)

```
subsystems/
├── common-overview.md        ← ⚠️ "common" 是技术包名
├── employee-overview.md
└── attendance-overview.md
modules/
├── common/                   ← ⚠️ 技术层目录！
│   ├── api-response.md
│   └── auth-context.md
├── employee/
│   ├── employee-entity.md
│   ├── employee-controller.md ← ⚠️ 以 Controller 命名
│   ├── employee-service.md
│   └── employee-service-test.md
└── attendance/
    ├── attendance-controller.md ← ⚠️ 同上
    └── attendance-service.md
```

**问题**: `common` 直接对应 Java 包名 `com.campus.common`，且子文档命名用了 `controller`/`service` 技术层后缀。这正是 SKILL.md 规则 #2 所禁止的。

### Before (完整 SKILL.md)

```
systems/campus-hr-backend/
├── overview.md
└── modules/
    ├── employee-management/       ← ✅ 业务名
    │   ├── overview.md
    │   ├── interface-get-employees.md
    │   ├── interface-post-employees.md
    │   ├── interface-put-resign.md
    │   └── interface-put-transfer.md
    └── attendance-management/     ← ✅ 业务名
        ├── overview.md
        ├── interface-get-monthly-summary.md
        ├── interface-post-anomalies.md
        └── interface-post-overtime-approve.md
```

**优点**: 模块命名完全符合业务能力（employee-management, attendance-management），命名规范一致（`interface-{method}-{name}`），无技术层模块。

**问题**: 只有一个子系统 `campus-hr-backend`（这本身就是技术名），且未单独文档化 ApiResponse/AuthContext（它们通过 module-map.json 和接口文档内的上下文引用被间接覆盖）。

### After (仅 Gene)

```
员工管理/                         ← ✅ 中文业务名
├── overview.md
├── 员工入职.md
├── 部门调动.md
└── 员工离职.md
考勤管理/                         ← ✅ 中文业务名
├── overview.md
├── 月度考勤汇总.md
├── 异常考勤标记.md
└── 加班审批.md
公共基础设施/                     ← ⚠️ 可接受但非必要
├── overview.md
├── 统一响应包装.md
└── 认证上下文.md
```

**优点**: 中文业务命名直观，文档用动词描述业务（入职/调动/离职），结构扁平无需 `systems/modules` 嵌套。

**可讨论**: `公共基础设施` 是为 2 个工具类建的独立模块。它不是技术层命名（如 Controller/Service），但也不是核心业务能力。Gene 的 AVOID 未明确禁止此类命名。

## 三、内容质量对比

### 3.1 INDEX.md 开篇比较

**Baseline** — 英语，技术架构导向：
> "The system follows a classic three-layer Spring architecture: Controller → Service → Repository"

**Before** — 中文，业务导向但有冗余结构描述：
> "本项目为单体后端，目前不涉及跨系统业务链路"

**After** — 中文，业务模块导向，最简洁：
> "校园管理系统的人力资源与考勤模块...提供员工生命周期管理和考勤业务处理能力"

### 3.2 文档粒度

| | Baseline | Before | After |
|------|:--:|:--:|:--:|
| 每模块平均文档数 | 2-4 | 4-5 | 3-4 |
| 文档命名风格 | 技术层（controller/service） | 接口规范（interface-get-） | 业务动词（入职/调动） |
| 源码引用 | ✅ | ✅ | ✅ |
| 规则覆盖率 | ✅ | ✅ | ✅ |

## 四、关键发现

### 发现 1: Before（完整 Skill）在结构规范上最好

完整的 SKILL.md 提供的 17 步初始化流程、详细的目录规范、module-map.json 要求，这些**没有写进 Gene**，导致 After（Gene）agent 缺少 `module-map.json` 和使用了一级扁平目录（而非 `systems/<sub>/modules/<mod>/` 三层结构）。

**这意味着**: Gene 的 compact 性质必然丢失一些结构性细节。对于 campus-repo-knowledge 这种高度结构化的任务，这些细节**确实有价值**。

### 发现 2: After（Gene）在命名的"业务直觉"上最好

`员工入职.md` 比 `interface-post-employees.md` 对中文团队更友好。After 用动词短语命名，Before 用技术前缀命名。Gene 没有规定命名格式，agent 自由选择了更自然的命名方式。

### 发现 3: Baseline 暴露了没有指导时的退化方向

没有指导时，模型自然地按技术分层（controller/service/common）组织文档——这恰好是 SKILL.md 要纠正的行为。这说明**有指导肯定比没有好**。

### 发现 4: Gene 效率优势显著，但有结构信息损失

| | Before (3,153 tokens) | After (280 tokens) |
|------|:--:|:--:|
| 指导 token | 3,153 | 280 (省 91%) |
| 产出大小 | 74,522 | 58,274 (精简约 22%) |
| 结构规范遵循 | ✅ 严格 | ⚠️ 部分偏离 |
| module-map.json | ✅ | ❌ |
| 业务模块命名 | ✅ 英文规范 | ✅ 中文直观 |
| 技术层残留 | 0 | 0（公共基础设施可接受）|

---

## 五、诚实结论

### Gene 的适用边界

| 场景 | Gene 是否足够 |
|------|:--:|
| 任务的核心控制逻辑（策略、AVOID） | ✅ 280 tokens 足够 |
| 高度结构化的目录/文件约定 | ❌ 需要 Skill 的详细规范 |
| 命名风格指导 | ⚠️ 可好可坏（取决于 agent 自行判断） |
| 辅助文件的生成（如 module-map.json） | ❌ Gene 未提及，agent 不会生成 |
| 防止基础反模式 | ✅ AVOID 信号有效 |

### 对 campus-repo-knowledge 的建议

**最佳方案是分层混合**——不是非此即彼：

```
SKILL.md (~500 tokens):
  ├── Gene section (~280 tokens)     ← 控制指令 (路由/策略/AVOID/验证)
  └── 结构规范 (~220 tokens)          ← 必要的目录格式/命名约定
references/FULL.md                    ← 完整原始文档（人类深入学习时看）
```

这样模型在推理时拿到 ~500 tokens（而非 3,153），既保留了 Gene 的控制信号，又不丢失结构规范。这比纯 Gene（280 tokens，丢失结构信息）和纯 Skill（3,153 tokens，信号稀释）都更优。

---

*实验日期: 2026-07-29*
