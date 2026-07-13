# Campus Repo Memory 使用说明

Campus Repo Memory 是一个给代码仓用的知识归档 skill。它不会强迫你走 SDD，也不是单纯生成一份代码图谱。它的目标更朴素：在代码仓里维护一个 `.repo-knowledge/` 文件夹，把代码结构、需求理解、实现记录、验证结果和关键决策都留下来。下次 agent 接到类似需求时，可以先读这些 Markdown，再去看代码，不用每次都从零开始猜。

## 安装

如果希望 Codex 自动识别这个 skill，把整个仓库目录复制或移动到 Codex skills 目录：

```text
C:\Users\Jiang\.codex\skills\campus-repo-memory
```

临时使用也可以不安装，直接在提示词里指定路径：

```text
Use $campus-repo-memory at D:\codex\campus-repo-memory ...
```

如果已经在这个仓库目录下，也可以直接运行脚本：

```powershell
python scripts\repo_knowledge.py --help
```

## 场景一：给新代码仓初始化知识库

在目标代码仓上运行：

```powershell
python <skill>\scripts\repo_knowledge.py init --repo <repo>
```

例如：

```powershell
python D:\codex\campus-repo-memory\scripts\repo_knowledge.py init --repo D:\codex\your-project
```

执行后，目标代码仓里会出现：

```text
.repo-knowledge/
  INDEX.md
  project.md
  inventory/
  modules/
  features/
  decisions/
  inbox/
```

这一步只会生成第一版骨架和代码扫描结果。真正有价值的部分，是让 agent 继续读代码，把 `TBD` 补成准确的项目知识。可以这样说：

```text
Use $campus-repo-memory to initialize knowledge for this repository.
先读 .repo-knowledge 里生成的内容，再检查主要模块，把 project.md 和 modules/*/overview.md 里的 TBD 补完整。
重点记录模块职责、入口文件、已有行为、测试方式和后续改动时要注意的规则。
```

初始化完成后，建议把 `.repo-knowledge/` 一起提交进代码仓。它本来就是代码仓的一部分，不是临时缓存。

## 场景二：有增量需求时先读旧知识，再建需求档案

假设你要给日志模块增加导出功能，可以先查已有知识：

```powershell
python <skill>\scripts\repo_knowledge.py context --repo <repo> --query "日志 导出"
```

然后创建一个需求文件夹：

```powershell
python <skill>\scripts\repo_knowledge.py new-feature --repo <repo> --title "Add log export"
```

它会生成类似这样的目录：

```text
.repo-knowledge/features/2026-07-13-add-log-export/
  request.md
  spec.md
  implementation.md
  verification.md
```

这几个文件分别放：

- `request.md`：用户到底想要什么，哪些属于范围内，哪些明确不做。
- `spec.md`：最终行为是什么，影响哪些模块，边界条件怎么处理。
- `implementation.md`：实际改了哪些文件，为什么这么改，有没有迁移或配置点。
- `verification.md`：跑了哪些测试，做了哪些手动验证，还有什么风险没覆盖。

你可以手写代码，也可以用 Superpowers、SDD 或别的流程。这个 skill 只负责把最后值得留下的东西整理进 `.repo-knowledge/`。如果 Superpowers 生成了 `requirements.md`、`design.md`、`tasks.md` 之类的文件，不需要整篇复制，只把以后还会用到的需求理解、设计约束和验证结论归档进 feature 文件夹。

## 场景三：开发完成后归档本次改动

功能验证通过后，运行：

```powershell
python <skill>\scripts\repo_knowledge.py archive --repo <repo> --feature <feature-id> --summary "实现了日志 CSV 导出，支持按级别过滤。" --files "src/api/logs.ts,src/logs/exporter.ts"
```

`<feature-id>` 就是 feature 目录名，例如：

```text
2026-07-13-add-log-export
```

这条命令会给 `implementation.md` 追加一段归档记录，并刷新索引。命令生成的是机械记录，最好再让 agent 检查一遍，把关键意图补进去：

```text
Use $campus-repo-memory to archive this completed change.
请结合 git diff、测试结果和现有 .repo-knowledge 内容，更新相关 feature、module overview、decision 和 INDEX。
不要只列文件名，要记录这个需求为什么这么做、下次改同一块时要注意什么。
```

## 场景四：有人没用这个 skill 改了代码，事后同步

如果代码已经变了，但 `.repo-knowledge/` 没跟上，可以生成一份待整理记录：

```powershell
python <skill>\scripts\repo_knowledge.py sync --repo <repo> --since HEAD~1
```

如果只是想看当前工作区未提交的变化：

```powershell
python <skill>\scripts\repo_knowledge.py sync --repo <repo>
```

生成的文件会放在：

```text
.repo-knowledge/inbox/sync-YYYY-MM-DD-HHMMSS.md
```

`inbox/` 只是暂存区，不是最终文档。后续需要把里面的发现整理到对应位置：

- 改了整体架构或命令，更新 `project.md`。
- 改了某个模块行为，更新 `modules/<module>/overview.md`。
- 补上某个需求背景，新增或更新 `features/<date>-<slug>/`。
- 出现长期设计取舍，新增 `decisions/NNNN-title.md`。

## 场景五：让 agent 快速理解代码

新需求开始前，可以这样提示：

```text
Use $campus-repo-memory.
先读 .repo-knowledge/INDEX.md，再根据我的需求运行 context。
只打开命中的 module、feature、decision 和相关源码文件。
在写方案前，先告诉我：这个需求归哪个模块管、已有行为是什么、历史上有什么相关需求、有哪些决策会限制这次改动。
```

对应命令：

```powershell
python <skill>\scripts\repo_knowledge.py context --repo <repo> --query "<你的需求关键词>"
```

这一步的价值是减少无效扫描。agent 不需要一上来读完整个仓库，而是先从索引和历史需求里找到方向，再去看真正相关的代码。

## 常用命令速查

```powershell
# 初始化
python <skill>\scripts\repo_knowledge.py init --repo <repo>

# 重新扫描并更新索引
python <skill>\scripts\repo_knowledge.py scan --repo <repo> --update

# 新建需求档案
python <skill>\scripts\repo_knowledge.py new-feature --repo <repo> --title "Add log export"

# 完成后归档
python <skill>\scripts\repo_knowledge.py archive --repo <repo> --feature 2026-07-13-add-log-export --summary "实现了日志导出。" --files "src/api/logs.ts"

# 同步未归档代码变化
python <skill>\scripts\repo_knowledge.py sync --repo <repo> --since HEAD~1

# 按需求关键词找上下文
python <skill>\scripts\repo_knowledge.py context --repo <repo> --query "日志 导出 条件"
```

## 设计方案

这个 skill 的核心设计是把 agent 的“临时理解”变成仓库里的“长期资料”。很多工具能帮助 agent 更快看懂代码，比如 repo map、code graph、code memory，但它们通常更偏代码结构；而实际开发里，真正难恢复的是需求上下文：当时为什么这么做，哪些边界被讨论过，哪些方案被放弃了，验证到什么程度。

所以 `.repo-knowledge/` 分成几类内容：

- `INDEX.md`：入口索引。新 agent 先读它，知道该去哪看。
- `project.md`：项目级知识。放架构、命令、约定、风险和术语。
- `inventory/`：代码扫描结果。偏机械，用来定位文件和模块。
- `modules/`：模块卡片。记录职责、主文件、接口、数据流、测试和维护注意点。
- `features/`：需求历史。每个需求一组 `request/spec/implementation/verification`。
- `decisions/`：长期决策。类似 ADR，记录为什么选这个方案，以及后果。
- `inbox/`：同步暂存区。用于接住那些还没整理进正式文档的代码变化。

脚本负责做稳定、重复、容易出错的部分，比如建目录、扫文件、生成索引、读 git diff。业务理解仍然交给 agent 和人来补，因为这类内容不能只靠自动扫描生成。

## 为什么这样做

第一，它是 Markdown 文件，能进 git，能 code review，能被人直接改。不会因为换了机器、换了 agent、换了 MCP 服务就丢掉。

第二，它把“代码事实”和“需求理解”放在一起，但不混成一坨。模块卡负责说明代码现在怎么组织，feature 负责说明某次需求为什么这样落地，decision 负责说明长期取舍。

第三，它不绑定开发模式。你可以手写代码，可以用 SDD，也可以用 Superpowers。只要最后把有用的理解归档回来，下次就能复用。

第四，它允许慢同步。初始化和事后同步可以花久一点，甚至可以分模块慢慢补；但一旦补过，下次处理同一块需求会快很多。

第五，它对语言不强绑定。当前扫描重点照顾 Java、TypeScript/Vue 3 和 C，但目录结构和归档方法本身适用于大多数代码仓。

## 已验证内容

我用一个混合语言样例仓测过以下路径：

- TypeScript API/store 文件
- Java 日志服务
- C header/source 导出函数

验证过的命令：

```powershell
python <skill>\scripts\repo_knowledge.py init --repo <sample>
python <skill>\scripts\repo_knowledge.py new-feature --repo <sample> --title "Add log export"
python <skill>\scripts\repo_knowledge.py archive --repo <sample> --feature 2026-07-13-add-log-export --summary "Implemented CSV log export for filtered logs and documented acceptance criteria." --files "src/api/logs.ts,src/c/log_export.c,include/log_export.h"
python <skill>\scripts\repo_knowledge.py sync --repo <sample>
python <skill>\scripts\repo_knowledge.py context --repo <sample> --query "exportLogs"
python C:\Users\Jiang\.codex\skills\.system\skill-creator\scripts\quick_validate.py <skill>
```

验证时顺手修了两个问题：

- Java 包路径一开始分得太粗，`com.demo.logs` 会被归到 `com`。现在会归到更有意义的 `logs`。
- `git status --short` 的路径解析在某些情况下会吞掉首字母。现在已经改成按状态前缀解析，并且会过滤 `.repo-knowledge/` 自身变化，减少同步噪音。
