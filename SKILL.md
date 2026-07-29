---
name: campus-repo-knowledge
description: 为代码仓生成、查询和维护面向人类与 Agent 的实现级分层中文知识库。用于初始化或升级 `.repo-knowledge/`，按“项目总览→子系统总览→业务模块 overview→每个页面/接口/功能点的独立实现文档→源码与测试”渐进理解业务。每个模块必须拥有自己的目录、overview 导航及多份实现细节文档；任务结束前必须清除所有占位词并通过硬性质量门禁。前端逐页面覆盖 View、重要组件、状态、交互和 API 协作；后端逐接口或用例覆盖规则分支、实现算法、数据、事务、并发和副作用。也用于需求完成或未知代码改动后同步知识；适用于单体、多模块、前后端同仓及多语言项目。
---

## 策略基因 (Strategy Gene)

<!-- 模型优先读取此 section。约 280 tokens。详见 docs/what-is-gene.md -->

**触发词**: repo-knowledge, .repo-knowledge, 知识库, 代码文档, 业务模块, INDEX.md, module-map, doctor

**一句话**: 在目标仓库建立分层中文知识库 (INDEX→子系统→模块→实现细节)，通过渐进式源码调查产出让新人独立理解业务的开发手册。

**怎么做**:
1. 判断场景: .repo-knowledge/ 不存在→初始化，用户问代码/接口→分层查询，开发完成→归档，代码变更→同步
2. 初始化时先运行 init 脚本，再编辑 module-map.json 把 Controller/Service/Mapper 等技术类归并到业务模块
3. 查询必须渐进: INDEX.md → 子系统 overview → 模块 overview → 实现文档 → 源码，禁止跳过
4. 每个业务模块至少 overview.md + 2 份实现细节文档，后端按接口拆分，前端按页面拆分
5. 归档/同步后必须运行 doctor --strict，警告即失败，回源码修正直到"错误 0，警告 0"

**不要做**:
- 不要把 Controller/Service/Mapper/Repository 等技术层目录名当业务模块名
- 不要把多个模块的实现平铺在一个 overview.md 里
- 不要跳过渐进加载直接全局搜索源码
- 不要在文档里保留 "待补充"/"待调查"/"TODO"/"TBD" 占位词
- 不要用路由表/接口表/文件清单冒充知识文档
- 不要在未阅读源码和测试的情况下写业务规则描述

**边界**: module-map.json 有技术层碎片→归并到业务模块，大型仓库→按 subagent-workflow.md 分派，v1/v2/v3 旧格式→先迁移目录再升级

**验证**: `python <skill>/scripts/repo_knowledge.py doctor --repo <repo> --strict`

---

# Campus Repo Knowledge

在目标仓库维护 `.repo-knowledge/`。它是普通 Markdown 工程手册，不是只供 Agent 使用的向量索引，也不是脚本生成的文件清单。

## 不可妥协的结果

1. 建立严格的分层导航：`INDEX.md` → `systems/<子系统>/overview.md` → `systems/<子系统>/modules/<模块>/overview.md` → 每个页面/接口/功能点的实现文档 → 源码与测试。
2. 为每个稳定业务模块建立独立目录和“开发手册”。禁止把多个模块 Markdown 平铺在 `modules/` 下；不得用 controller/service/repository、views/components/api 等技术层代替业务模块。
3. 前端手册必须解释页面总体流程、View 的编排职责、重要组件树及每个组件的业务作用、props/emits、状态归属、用户交互、接口协作与边界场景。
4. 后端手册必须解释业务用例、每条关键规则及触发条件、完整实现步骤、查询/计算逻辑、状态和数据变化、事务/并发/幂等、外部副作用与失败恢复；接口入参出参只是其中一小部分。
5. 文档须让没读过源码的人理解。先解释业务目的、用户场景、规则和流程，再给代码标识与路径；不要堆类名、符号、路由或文件列表冒充知识。
6. 完成标准是：一个只懂该语言的开发者，不打开源码也能复述业务、主要流程和关键规则，并知道增加一个相邻能力通常要改哪里、保持什么契约、如何验证。
7. 所有代码事实附仓库相对路径和关键符号；推断明确标注，文档与已验证代码冲突时立即修正文档。
8. 总览只负责业务地图、总体流程和细节路由。实现细节必须落到同目录独立 Markdown：后端原则上一个接口/消费者/任务/核心用例一份；前端原则上一个列表页、详情页、编辑页或独立 View 一份。禁止把全部实现继续塞回 overview。
9. 最终知识库不得包含 `待补充`、`待调查`、`待核对`、`TODO`、`TBD`、模板变量或内部占位标记。发现一个就继续查源码、测试、配置和历史；确实无法确认时写成具体问题、已查证据和影响，不得保留占位句。

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
2. 只读命中的 `systems/<子系统>/overview.md`，从模块职责、接口/路由和检索词选择模块目录。
3. 先读 `systems/<子系统>/modules/<模块>/overview.md` 的“实现细节导航”，再只读命中的 `interface-*.md`、`use-case-*.md`、`page-*.md`、`feature-*.md` 或共享实现文档。
4. 理想情况下，模块目录内文档足以回答业务与实现问题；只打开链接的最少源码与测试，确认文档新鲜度或补充尚未归档的细节。
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
4. 编辑 `inventory/module-map.json`，按业务能力重新归并机械候选。将同一能力散落在 controller/service/repository、页面/API/store 中的实现映射到同一业务模块名；不得保留 `EmployeeMapper`、`EmployeeService` 等技术类名模块。运行 `scan --update` 使合并结果进入机械地图和导航，再迁移已有知识并清理孤立旧目录。
5. 除很小的仓库外，按 `references/subagent-workflow.md` 分派独立子系统或模块。主 Agent 负责全局导航、合并、冲突处理和验收。
6. 对每个模块执行 `references/module-research.md` 的取证协议。必须从入口追到业务结果和失败路径，阅读关键实现而不是只读类型、注解、路由和调用名称。
7. 前端逐个阅读根 View、业务组件、composable/store、路由、API 客户端和测试，重建用户流程、组件协作、状态生命周期与交互分支。
8. 后端逐个业务用例从入口追到业务服务、领域规则、数据访问、事件/外部依赖和测试，解释每个关键条件、转换、查询和数据变化为什么存在。
9. `overview.md` 只写模块边界、业务地图、总体流程、规则摘要和实现细节导航。每个链接必须说明“什么问题读这份文档”，不能只列文件名。
10. 每个模块至少包含 `overview.md` 和两份实现细节文档。后端为每个重要 HTTP/RPC/GraphQL 接口、事件消费者、定时任务、CLI 或公开用例建立独立文档；HTTP 必须按“方法 + 完整路径”区分，同一路径的 GET/POST 不得合并。前端为每个列表页、详情页、编辑页、弹窗型业务 View 或其他独立用户能力建立独立文档。共享组件/状态和开发验证另立文档。即使代码很少，也不能只有 overview。
11. 后端细节文档必须从入口逐步追到业务服务、领域规则、查询/持久化/外部依赖，包含逐字段业务语义表，并在实现链路中至少给出两个 `文件#符号` 锚点。前端页面文档必须包含重要组件职责/契约表和逐接口协作/数据转换表，再从路由与首屏初始化追到用户动作、状态生命周期、反馈和边界。静态页面也要明确证明“无 API/无业务动作”，不能套通用描述。
12. 回填子系统总览的业务旅程、模块关系、模块职责、接口/路由/别名检索词，再回填根总览的跨系统业务链路和新人阅读路径。
13. 运行 `scan --update` 仅刷新机械清单并补建缺失的接口/页面骨架，不指望脚本替代源码调查。扫描可能发现新入口，因此必须在它之后做最终清理。
14. 逐模块核对机械清单：每条公开后端入口、每个用户可达前端页面和每个独立功能点，都必须在 overview 导航中有唯一落点；不能用一份笼统 `implementation.md` 代替所有细节。
15. 运行 `doctor --strict`。v5 中警告也会无条件导致失败；它会检查模块至少三份文档、overview 链接、接口/页面覆盖、实现步骤、组件树、章节深度、源码证据和占位残留。
16. 若失败，逐项回到源码调查并补写，重复 `scan --update` → `doctor --strict`，直到输出“错误 0，警告 0”。禁止通过删除章节、合并掉独立接口/页面、删除证据或改成模糊空话来通过。
17. 再独立运行 `rg -n "待补充|待调查|待核对|KNOWLEDGE_TODO|TODO|TBD" .repo-knowledge -g "*.md"`；必须没有输出。然后执行新人上手验收，任一步未通过都不能结束任务。

升级现有知识库时先读 `inventory/schema-version`。v1/v2/v3 先迁移目录；v4 即使已有完整 `overview.md`，也必须运行 `scan --update` 建立细节骨架，再按源码拆出逐接口、逐页面或逐功能点文档并回填 overview 导航。不得只改版本号。

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
python <skill>/scripts/repo_knowledge.py upgrade-layout --repo <repo>
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
