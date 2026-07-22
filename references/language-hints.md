# 语言扫描提示

知识库结构与语言无关，下面只用于提高首次扫描和模块划分的准确度。

## Java

优先查看 `pom.xml`、`build.gradle`、`settings.gradle`、`src/main/java` 和 `src/test/java`。从 package、controller、service、repository、entity、配置类与测试组织推断模块边界。

模块文档应从 controller 追进 service/use case 的方法体、领域规则、repository 查询、模型转换和测试。记录参数校验、权限范围、`@Transactional` 边界、异常映射、缓存/事件及关键查询的业务含义。多模块 Maven/Gradle 项目先识别构建子系统，再按业务能力把 controller、service、repository 合并成模块，不能把技术层直接当作最终模块。

## TypeScript / Vue 3

优先查看 `package.json`、`vite.config.*`、`tsconfig.json`、`src/main.ts`、router、stores、components、views、composables 和 API 客户端。

模块文档应完整阅读根 View 的 template/script/setup、重要业务组件、Pinia store、composable、路由守卫和 API 调用前后逻辑。记录组件树与职责、props/emits、状态生命周期、watch/effect、字段联动、异步竞态、错误反馈和用户成功/失败流程。不要把每个组件或 `views/api/stores` 技术目录当成独立模块，按业务能力聚合。

## C

优先查看 `CMakeLists.txt`、`Makefile`、`meson.build`、`src/`、`include/` 和 `tests/`。把公共头文件、导出函数、编译目标、平台条件和测试夹具视为重要边界。

模块文档应明确内存/资源所有权、生命周期、线程或中断约束、编译宏、平台假设、错误码和测试方式。公共头文件通常比源文件目录更能说明对外契约。

## 通用原则

- 构建文件是架构证据，测试是行为证据，提交信息只能作为需求意图线索。
- 公开头文件、导出类、路由和 API 客户端通常标志模块边界。
- 标明生成文件及其来源，不把生成文件作为主要文档锚点。
- 缺少语言解析器时，先按路径和可识别声明生成保守地图，再由 subagent 阅读源码修正。
- 同一概念跨前后端或跨语言时，分别记录模块职责，并在数据/API 契约处建立双向链接。
