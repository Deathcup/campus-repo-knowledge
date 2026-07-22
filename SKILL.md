---
name: campus-repo-knowledge
description: 为代码仓生成、查询和维护面向人类与 Agent 的分层中文知识库。用于初始化或升级 `.repo-knowledge/`，按“项目总览→前后端等子系统总览→业务模块独立文档→源码与测试”渐进定位实现，详细归档每个模块的职责、接口、调用链、数据流、配置、测试和维护风险，以及在需求完成或未知代码改动后同步知识。适用于单体、多模块、前后端同仓及多语言项目；大型初始化和未知范围同步使用 subagent 分片调查。
---

# Campus Repo Knowledge

在目标仓库维护 `.repo-knowledge/`。它是普通 Markdown 工程手册，不是只供 Agent 使用的向量索引，也不是脚本生成的文件清单。

## 不可妥协的结果

1. 建立严格的三级导航：`INDEX.md` → `systems/<子系统>/overview.md` → `systems/<子系统>/modules/<模块>.md`。
2. 为每个稳定业务模块建立一份独立文档。不得只写仓库概览，也不得用 controller/service/repository 等技术层代替业务模块。
3. 模块文档必须覆盖相关接口及其实现方式：入口、参数、鉴权、调用链、关键分支、数据访问、异常、配置和测试证据。
4. 文档须让没读过源码的人理解。先解释业务目的和行为，再给代码标识与路径；不要堆类名、符号或文件列表冒充说明。
5. 所有代码事实附仓库相对路径，关键接口尽量附符号名；推断明确标注，文档与已验证代码冲突时立即修正文档。
6. 总览只负责摘要和路由，详细实现只放模块文档。上层必须链接下层，下层必须链接必要源码、测试、需求和决策。

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
3. 读命中的模块文档，找到目标接口、实现链路、证据路径、测试和约束。
4. 只打开模块文档链接的最少源码与测试，核对当前实现。
5. 若上层总览无法完成路由，再运行：
   `python <skill>/scripts/repo_knowledge.py context --repo <repo> --query "<问题>"`
6. 如果不得不靠机械地图或全局检索找到答案，回答问题后补回缺失的总览路由或模块内容。

例如查询“后端日志 `eslog/query` 接口怎么实现”：先由根总览选择后端，再由后端总览选择日志模块，再在日志模块文档读取该接口的入口、Service、查询条件、ES/数据库访问、返回值和测试，最后核对所链接源码。

回答时说明导航链和代码证据，并区分已确认事实、推断和未知项。知识库用于缩小范围，不替代源码验证。

## 初始化/升级

1. 阅读 `references/archive-schema.md` 和 `references/writing-guide.md`。扫描对应语言时再读 `references/language-hints.md`。
2. 在内部运行：
   `python <skill>/scripts/repo_knowledge.py init --repo <repo>`
3. 盘点构建单元、部署单元、前后端边界、启动入口、API 边界和测试位置，修正脚本的候选子系统。
4. 按业务能力重新划分模块。将同一能力散落在 controller/service/repository、页面/API/store 中的实现合并为一个模块；把职责不同的大目录拆开。
5. 除很小的仓库外，按 `references/subagent-workflow.md` 分派独立子系统或模块。主 Agent 负责全局导航、合并、冲突处理和验收。
6. 按源码与测试逐份完成模块文档；发现公开 HTTP/RPC/CLI/事件/库接口时，必须在对应模块的“接口目录”和“接口与实现详解”中落档。
7. 回填每个子系统总览的模块职责、接口/路由/别名检索词，再回填根总览的子系统边界和跨系统主链路。
8. 运行 `scan --update` 仅刷新机械清单和补建缺失骨架，不指望脚本替代源码调查。
9. 运行 `doctor --strict`。初始化完成时不得有坏链、缺失模块文档或无解释的“待补充”；真实未知项改写为具体问题、证据和确认人/方向。

如果旧知识库使用 `project.md` 和 `modules/*/overview.md`，先保留内容，再把仓库级结论合并到 `INDEX.md`，把模块内容迁入对应 `systems/<子系统>/modules/*.md`。确认新导航完整后才能移除旧入口。

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
3. 更新每个受影响模块的接口目录、实现详解、数据流、配置、测试和风险。
4. 更新子系统总览中的模块摘要与检索词；跨子系统边界变化时再更新根总览。
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
- 编写面向人的模块文档、接口说明和总览摘要时读 `references/writing-guide.md`。
- 扫描特定语言或框架时读 `references/language-hints.md` 的对应章节。
- 初始化大型仓库或同步未知范围改动时读 `references/subagent-workflow.md`。
