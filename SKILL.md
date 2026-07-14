---
name: campus-repo-knowledge
description: 为代码仓建立和维护可版本化的中文知识库，归档项目结构、模块职责、需求背景、实现记录、验证结论与关键决策。用于初始化仓库知识、开始增量需求前快速理解相关代码和历史需求、开发完成后反向归档、同步未经过本技能的代码改动，以及维护 Java、TypeScript/Vue 3、C 或其他语言项目的长期知识。大型初始化和未知范围同步必须优先调用 subagent 分片处理，避免单个 Agent 超出上下文。
---

# Campus Repo Knowledge

## 目标

在目标代码仓根目录维护 `.repo-knowledge/`。它是随代码一同版本管理的中文知识层，记录代码现在怎样工作、需求为什么这样设计、模块在哪里、哪些决策不能随意破坏，以及每次改动最终验证到了什么程度。

可以配合 Superpowers、SDD、代码图谱或 Repo Map 使用。其他工具负责当前开发过程时，把以后仍有价值的结论整理回知识库；不要照搬完整任务清单或临时推理。

## 总体规则

1. 面向用户和知识库的内容使用中文；代码标识、文件路径、命令、协议字段保留原文。
2. 正常情况下由 Agent 调用 `scripts/repo_knowledge.py`，不要要求用户手动执行脚本。
3. 代码与知识库冲突时，以已验证的代码和测试为准，并立即修正文档。
4. 只记录可复用的事实、需求意图、约束、取舍与验证证据，避免堆积自动生成的长清单。
5. 新增模块、需求或决策后更新 `INDEX.md`，所有引用尽量使用仓库相对路径。

## 任务路由

先判断用户属于哪种场景：

- `.repo-knowledge/` 不存在：执行“初始化仓库”。
- 用户提出新需求或询问代码：执行“快速理解”，需要开发时再执行“增量需求”。
- 本轮开发已经完成：执行“完成后归档”。
- 代码已变化但知识库可能落后，且改动范围不明确：执行“未知改动同步”。
- 只需修正文档：读取相关知识与代码，直接更新规范位置并刷新索引。

## 快速理解

按最小上下文原则读取：

1. `.repo-knowledge/INDEX.md`
2. `.repo-knowledge/project.md`
3. 在内部运行 `context --query "<需求关键词>"`
4. 命中的模块卡、历史需求和决策
5. 上述文档链接的源码与测试

写方案或代码前先确认：由哪个模块负责、当前行为是什么、哪些历史需求塑造了它、哪些长期决策限制本次改动。知识库不能替代源码验证，只用于缩小阅读范围。

## 初始化仓库

1. 在内部运行：
   `python <skill>/scripts/repo_knowledge.py init --repo <repo>`
2. 先用廉价盘点识别语言、构建入口、目录边界、模块候选和测试位置。
3. 除了很小的仓库，必须按 `references/subagent-workflow.md` 分配多个 subagent。主 Agent 不得自己把整个仓库逐文件读入上下文。
4. 让每个 subagent 只研究一个模块或一个横切主题，并返回结构化中文结论与证据路径。
5. 主 Agent 合并结果，补全 `project.md`、模块卡、必要的决策记录和待确认项。
6. 检查索引链接、重复结论、模块边界和遗留 `待补充`，再运行 `scan --update` 刷新机械清单。

初始化不是“脚本跑完即完成”。只有项目入口、关键模块职责、主要运行链路、测试方式和高风险约束经过源码核对后，才算完成。

## 增量需求

1. 先执行“快速理解”，读取与需求最相关的知识和源码。
2. 在内部运行：
   `python <skill>/scripts/repo_knowledge.py new-feature --repo <repo> --title "<简短中文标题>"`
3. 根据用户讨论逐步维护：
   - `request.md`：目标、业务背景、范围、非目标、约束、待确认问题。
   - `spec.md`：预期行为、受影响模块、输入输出、异常边界、兼容性、验收条件。
   - `implementation.md`：最终实现、变更文件、关键取舍、配置或迁移。
   - `verification.md`：自动化测试、手动检查、测试数据、已知缺口。
4. 使用用户选择的开发方式完成实现，不强制 SDD。
5. 需求或实现发生变化时同步修正文档，不保留已失效方案冒充最终结论。

如果 Superpowers 或其他流程产生了 `requirements.md`、`design.md`、`tasks.md` 等文件，只提炼长期有效的内容；原文件仍在仓库时使用相对链接。

## 完成后归档

功能验证通过后：

1. 读取本轮对话中的需求结论、最终 diff、提交记录（如有）和测试结果。
2. 若尚无需求目录，补建一个；不要因为开发时没用本技能就跳过需求背景。
3. 在内部运行 `archive` 写入机械变更记录，然后人工整理四份需求文档。
4. 更新受影响的模块卡；只有长期、跨需求的取舍才写入 `decisions/`。
5. 更新 `INDEX.md`，确认文档所述行为与最终代码一致。
6. 在最终回复中简要说明归档了什么，以及仍有哪些知识缺口。

## 未知改动同步

用于他人未通过本技能改动代码、跨多个提交补文档，或无法预先知道受影响模块的情况。

1. 确定比较基线。优先使用用户给出的 ref；否则结合 git 历史、工作区状态和知识库最后记录判断，不能确定时记录假设。
2. 在内部运行 `sync --since <base-ref>` 生成 `inbox/sync-*.md`。
3. 先按目录、提交和依赖关系把变更聚成若干变更簇。
4. 除非变更很小，必须按 `references/subagent-workflow.md` 并行分派，每个 subagent 只检查一个变更簇及其必要依赖和测试。
5. 主 Agent 汇总“行为变化、需求意图推断、证据、置信度、待确认项”，再决定更新项目概览、模块卡、需求历史或决策。
6. 推断出来的需求背景必须明确标注“根据代码/提交推断”，不能写成已确认的用户意图。
7. 将持久结论移入正式文档，在 inbox 记录处理结果；完成前刷新索引并复核源码。

## Subagent 与上下文控制

初始化和未知改动同步默认使用 subagent。若当前运行环境没有 subagent 工具，则按相同分片方案串行处理，每完成一片就先写入临时汇总，释放细节上下文后再继续。

主 Agent 负责盘点、分片、派单、冲突消解、最终写入与验收；subagent 负责有限范围的源码调查，不负责定义全局架构。禁止让所有 subagent 各自全仓扫描，也禁止把完整仓库清单和其他模块全文塞进每个任务。具体协议、返回格式和提示词模板见 `references/subagent-workflow.md`。

## 内部命令

这些命令是 Agent 的实现工具，不是给用户的常规操作步骤：

```bash
python <skill>/scripts/repo_knowledge.py init --repo <repo>
python <skill>/scripts/repo_knowledge.py scan --repo <repo> --update
python <skill>/scripts/repo_knowledge.py new-feature --repo <repo> --title "增加日志导出"
python <skill>/scripts/repo_knowledge.py archive --repo <repo> --feature <feature-id> --summary "实现日志导出并补充过滤条件" --files "src/logs/exporter.ts,src/logs/api.ts"
python <skill>/scripts/repo_knowledge.py sync --repo <repo> --since HEAD~1
python <skill>/scripts/repo_knowledge.py context --repo <repo> --query "日志导出条件"
```

脚本只负责稳定的目录、扫描和索引操作。生成后必须由 Agent 结合需求、源码和测试补全内容。

## 按需读取参考资料

- 创建或修复知识库文件时，读取 `references/archive-schema.md`。
- 扫描 Java、TypeScript/Vue 3 或 C 项目时，读取 `references/language-hints.md` 中对应章节。
- 初始化大型仓库或同步未知范围改动时，必须读取 `references/subagent-workflow.md`。
