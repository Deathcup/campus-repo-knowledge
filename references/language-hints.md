# 语言扫描提示

知识库结构与语言无关，下面只用于提高首次扫描和模块划分的准确度。

## Java

优先查看 `pom.xml`、`build.gradle`、`settings.gradle`、`src/main/java` 和 `src/test/java`。从 package、controller、service、repository、entity、配置类与测试组织推断模块边界。

模块文档应记录包边界、公开 service/controller、持久化模型、框架约定、事务或权限等横切规则，以及测试风格。多模块 Maven/Gradle 项目先识别构建子系统，再按业务能力把 controller、service、repository 合并成模块，不能把技术层直接当作最终模块。

## TypeScript / Vue 3

优先查看 `package.json`、`vite.config.*`、`tsconfig.json`、`src/main.ts`、router、stores、components、views、composables 和 API 客户端。

模块文档应记录页面路由、Pinia 状态归属、API 边界、组件职责、组合式函数、路由守卫、生成类型来源和构建测试命令。不要把每个组件或 `views/api/stores` 技术目录当成独立模块，按业务能力聚合。

## C

优先查看 `CMakeLists.txt`、`Makefile`、`meson.build`、`src/`、`include/` 和 `tests/`。把公共头文件、导出函数、编译目标、平台条件和测试夹具视为重要边界。

模块文档应明确内存/资源所有权、生命周期、线程或中断约束、编译宏、平台假设、错误码和测试方式。公共头文件通常比源文件目录更能说明对外契约。

## 通用原则

- 构建文件是架构证据，测试是行为证据，提交信息只能作为需求意图线索。
- 公开头文件、导出类、路由和 API 客户端通常标志模块边界。
- 标明生成文件及其来源，不把生成文件作为主要文档锚点。
- 缺少语言解析器时，先按路径和可识别声明生成保守地图，再由 subagent 阅读源码修正。
- 同一概念跨前后端或跨语言时，分别记录模块职责，并在数据/API 契约处建立双向链接。
