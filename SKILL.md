---
name: campus-repo-knowledge
description: 为代码仓生成、查询和维护面向人类与 Agent 的深度分层中文知识库。用于初始化或升级 `.repo-knowledge/`，按“项目总览→前后端等子系统总览→业务模块开发手册→源码与测试”渐进理解业务。模块手册须让只懂开发语言、首次接触服务的人仅凭文档理解业务并开始开发：前端覆盖用户流程、View、重要组件、状态、交互和 API 协作；后端覆盖业务用例、规则分支、实现算法、数据、事务、并发和副作用。也用于需求完成或未知代码改动后同步知识；适用于单体、多模块、前后端同仓及多语言项目。
---

# Campus Repo Knowledge

在目标仓库维护 `.repo-knowledge/`。它是普通 Markdown 工程手册，不是只供 Agent 使用的向量索引，也不是脚本生成的文件清单。

## 不可妥协的结果

1. 建立严格的三级导航：`INDEX.md` → `systems/<子系统>/overview.md` → `systems/<子系统>/modules/<模块>.md`。
2. 为每个稳定业务模块建立一份独立的“开发手册”。不得只写仓库概览，也不得用 controller/service/repository、views/components/api 等技术层代替业务模块。
3. 前端手册必须解释页面总体流程、View 的编排职责、重要组件树及每个组件的业务作用、props/emits、状态归属、用户交互、接口协作与边界场景。
4. 后端手册必须解释业务用例、每条关键规则及触发条件、完整实现步骤、查询/计算逻辑、状态和数据变化、事务/并发/幂等、外部副作用与失败恢复；接口入参出参只是其中一小部分。
5. 文档须让没读过源码的人理解。先解释业务目的、用户场景、规则和流程，再给代码标识与路径；不要堆类名、符号、路由或文件列表冒充知识。
6. 完成标准是：一个只懂该语言的开发者，不打开源码也能复述业务、主要流程和关键规则，并知道增加一个相邻能力通常要改哪里、保持什么契约、如何验证。
7. 所有代码事实附仓库相对路径和关键符号；推断明确标注，文档与已验证代码冲突时立即修正文档。
8. 总览负责业务地图和路由，模块手册负责完整上下文。生成阶段以深度和完整性优先，不因节省 token 省略调查；查询阶段靠分层导航控制加载量。

## 任务路由

- `.repo-knowledge/` 不存在或只有空骨架：执行“初始化/升级”。
- 用户询问代码、接口或模块：执行“分层查询”。
- 开始新需求：先分层查询，再建立需求档案。
- 开发完成：执行“完成后归档”。
- 已有代码变化但知识库可能落后：执行“未知改动同步”。
- 只需修正文档：读取对应导航链和源码，直接更新规范位置并刷新总览。

## 分层查询

查询必须按顺序渐进加载，禁止先对全仓源码或全部知识文档做无差别搜索。

1. 只读 `.repo-knowledge/INDEX.md`，从子系统职责、代码范围和识别词选择前端、后端或其他子系统。
2. 只读命中的 `systems/<子系统>/overview.md`，从模块职责、接口/路由和检索词选择模块。
3. 读命中的模块开发手册，先理解业务背景、总体流程、组件/服务协作、规则与开发指南，再定位目标接口或代码。
4. 理想情况下，文档本身足以回答业务与实现问题；只打开手册链接的最少源码与测试，确认文档新鲜度或补充尚未归档的细节。
5. 若上层总览无法完成路由，再运行：
   `python <skill>/scripts/repo_knowledge.py context --repo <repo> --query "<问题>"`
6. 如果不得不靠机械地图或全局检索找到答案，回答问题后补回缺失的总览路由或模块内容。

例如查询“后端日志 `eslog/query` 接口怎么实现”：先由根总览选择后端，再由后端总览选择日志模块；模块手册应先说明日志查询服务于什么业务、谁能查询哪些数据、完整查询流程和规则，再解释入口、条件规范化、权限范围注入、ES DSL/数据库查询、分页映射、异常、性能假设和测试，最后核对所链接源码。

回答时说明导航链和代码证据，并区分已确认事实、推断和未知项。知识库用于缩小范围，不替代源码验证。

## 初始化/升级

1. 完整阅读 `references/archive-schema.md`、`references/module-research.md` 和 `references/writing-guide.md`。扫描对应语言时再读 `references/language-hints.md`。
2. 在内部运行：
   `python <skill>/scripts/repo_knowledge.py init --repo <repo>`
3. 盘点构建单元、部署单元、前后端边界、启动入口、API 边界和测试位置，修正脚本的候选子系统。
4. 按业务能力重新划分模块。将同一能力散落在 controller/service/repository、页面/API/store 中的实现合并为一个模块；把职责不同的大目录拆开。
5. 除很小的仓库外，按 `references/subagent-workflow.md` 分派独立子系统或模块。主 Agent 负责全局导航、合并、冲突处理和验收。
6. 对每个模块执行 `references/module-research.md` 的取证协议。必须从入口追到业务结果和失败路径，阅读关键实现而不是只读类型、注解、路由和调用名称。
7. 前端逐个阅读根 View、业务组件、composable/store、路由、API 客户端和测试，重建用户流程、组件协作、状态生命周期与交互分支。
8. 后端逐个业务用例从入口追到业务服务、领域规则、数据访问、事件/外部依赖和测试，解释每个关键条件、转换、查询和数据变化为什么存在。
9. 按源码与测试完成模块开发手册；公开 HTTP/RPC/CLI/事件/库接口只是手册的一部分，不能用接口表替代业务说明。
10. 回填子系统总览的业务旅程、模块关系、模块职责、接口/路由/别名检索词，再回填根总览的跨系统业务链路和新人阅读路径。
11. 运行 `scan --update` 仅刷新机械清单和补建缺失骨架，不指望脚本替代源码调查。
12. 运行 `doctor --strict`。它会拦截模板残留、短文档、浅章节、无编号流程、前端无组件树、后端无规则表和证据不足。真实未知项改写为具体问题、已查证据和确认方向。
13. 执行“新人上手验收”：随机选一个前端和一个后端模块，仅根据文档回答 `references/module-research.md` 的验收问题；答不出来就继续查源码和补文档。

升级现有知识库时先读 `inventory/schema-version`。v1 使用 `project.md` 和 `modules/*/overview.md`，须迁入新层级；v2 虽已有分层，但模块文档通常只覆盖接口定位，必须逐份按 v3 前端/后端深度标准重写，不能因为文件已经存在而跳过。确认新导航和新人开发手册完整后才能移除旧入口。

## 增量需求

1. 先执行分层查询并用源码/测试核实现有行为。
2. 运行：
   `python <skill>/scripts/repo_knowledge.py new-feature --repo <repo> --title "<中文标题>"`
3. 维护 `request.md`、`spec.md`、`implementation.md` 和 `verification.md`，分别记录意图、预期行为、最终实现和验证证据。
4. 开发中如果接口、模块边界或实现链路变化，同步模块文档和两级总览；不要等到最后留下不一致文档。
5. 不强制特定开发流程，不保存临时任务清单或已经失效的长篇方案。

## 完成后归档

1. 读取最终需求结论、diff、提交和测试结果；尚无需求目录时补建。
2. 可先运行 `archive` 追加机械变更记录，再人工整理四份需求文档。
3. 更新每个受影响模块的业务背景、用户/用例流程、组件或服务协作、业务规则、接口实现、数据、测试和开发指南；不能只更新接口表。
4. 更新子系统总览中的业务旅程、模块关系、摘要与检索词；跨子系统边界变化时再更新根总览。
5. 只有跨需求长期有效的取舍写入 `decisions/`。
6. 运行 `scan --update` 与 `doctor --strict`，确认所有描述与最终代码一致。

## 未知改动同步

1. 明确比较基线；不能确定时记录假设。
2. 运行 `sync --since <base-ref>` 生成 inbox 清单。
3. 按子系统、业务模块和行为把 diff 聚类；大型范围按 `references/subagent-workflow.md` 分片。
4. 区分行为事实和需求意图。后者无法确认时写“根据代码/提交推断”，附证据、置信度和待确认项。
5. 将持久结论移入模块、需求或决策文档，并更新两级总览路由。
6. 记录 inbox 去向，运行 `doctor --strict` 后完成同步。

## 内部命令

```bash
python <skill>/scripts/repo_knowledge.py init --repo <repo>
python <skill>/scripts/repo_knowledge.py scan --repo <repo> --update
python <skill>/scripts/repo_knowledge.py context --repo <repo> --query "后端日志 eslog/query"
python <skill>/scripts/repo_knowledge.py doctor --repo <repo> --strict
python <skill>/scripts/repo_knowledge.py new-feature --repo <repo> --title "增加日志导出"
python <skill>/scripts/repo_knowledge.py archive --repo <repo> --feature <feature-id> --summary "实现摘要" --files "path/a,path/b"
python <skill>/scripts/repo_knowledge.py sync --repo <repo> --since HEAD~1
```

这些命令只负责稳定的目录、扫描、导航候选和质量检查。Agent 必须结合源码、测试和需求完成真正的文档内容。

## 按需读取参考

- 建库、迁移、修复结构或验收时读 `references/archive-schema.md`。
- 调查每个前端/后端模块并判断是否达到新人可开发深度时读 `references/module-research.md`。
- 编写面向人的模块手册、业务流程、关键逻辑和总览摘要时读 `references/writing-guide.md`。
- 扫描特定语言或框架时读 `references/language-hints.md` 的对应章节。
- 初始化大型仓库或同步未知范围改动时读 `references/subagent-workflow.md`。
