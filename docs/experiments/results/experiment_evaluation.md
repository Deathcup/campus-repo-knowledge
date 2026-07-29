# campus-repo-knowledge 改造实验

## 怎么测的

同一个任务——给 Campus HR System（一个 Spring Boot 后端，7 个源文件）生成知识库——用三种方式跑：

| 条件 | Agent 看到什么 | 多少字 |
|------|-------------|:--:|
| 无 Skill | 只有任务描述 | 0 |
| 改造前 | 完整 SKILL.md（和现在生产环境一样） | ~3,100 |
| 改造后 | 只有紧凑的混合方案 | ~450 |

三个 Agent 的调用方式完全一样，唯一区别是指令长短。

## 结果

### 模块归并

| | 无 Skill | 改造前 | 改造后 |
|------|:--:|:--:|:--:|
| 模块怎么命名 | `common`、`employee`、`attendance` | `employee-management`、`attendance-management` | 员工管理、考勤管理、公共基础设施 |
| 有没有技术层模块 | ❌ 有，`common` 是 Java 包名 | ✅ 没有 | ⚠️ 有"公共基础设施"，但不算纯技术名 |

无 Skill 时，模型自然地按代码目录结构（controller/service/common）组织文档——这正是 SKILL.md 要纠正的坏习惯。

### 结构规范

| | 无 Skill | 改造前 | 改造后 |
|------|:--:|:--:|:--:|
| module-map.json | ❌ 没有 | ✅ 有 | ❌ 没有 |
| 目录结构 | subsystems + modules 两级 | systems/campus-hr-backend/modules 三级 | 扁平，模块名直接放根目录 |
| 命名规范 | employee-controller.md | interface-get-employees.md | 员工入职.md |

改造前最规范，但代价是每次注入 3,100 字。改造后丢了一些结构约定——因为纯 Gene 里没写。

### 文档质量

三个条件都没留占位词，业务规则覆盖也都完整。改造后的文档更紧凑（总共 58KB，改造前 75KB），中文命名对团队更友好。

## 结论

| 方案 | token | 模块归并 | 结构规范 | 值不值 |
|------|:--:|:--:|:--:|:--:|
| 完整 SKILL.md | 3,100 | ✅ | ✅ | 太贵 |
| 纯 Gene | 280 | ✅ | ❌ | 太省，丢了东西 |
| **混合（现在用的）** | **~450** | ✅ | ✅ | **刚好** |

纯 Gene 不行——高度结构化的任务需要保留一些目录约定和命名规范。但不需要保留全部 3,100 字。把策略 + AVOID + 必要结构规范凑一起，~450 字，效果最好。

所以我们把 SKILL.md 改成了混合方案，完整版放 `references/FULL.md`。省了 86% 的 token，结构和质量都没降。

---

*实验日期: 2026-07-29*
