# Language Hints

The archive is language-neutral, but these hints improve first-pass scanning.

## Java

Signals:

- `pom.xml`, `build.gradle`, `settings.gradle`
- `src/main/java`, `src/test/java`
- packages, controllers, services, repositories, entities, configuration classes

Module cards should record package boundaries, public services/controllers, persistence models, framework conventions, and test style.

## TypeScript / Vue 3

Signals:

- `package.json`, `vite.config.*`, `tsconfig.json`
- `src/main.ts`, `src/router`, `src/stores`, `src/components`, `src/views`
- composables, Pinia stores, API clients, route guards, generated API types

Module cards should record UI routes, store ownership, API boundaries, component responsibilities, and build/test commands.

## C

Signals:

- `CMakeLists.txt`, `Makefile`, `meson.build`
- `src/`, `include/`, `tests/`
- public headers, exported functions, compile flags, platform branches

Module cards should record headers as interfaces, ownership/lifetime rules, compile targets, platform assumptions, and test harnesses.

## General Heuristics

- Treat build files as architecture evidence.
- Treat tests as behavior evidence.
- Treat public headers, exported classes, routes, and API clients as module boundaries.
- Record generated files as generated and avoid making them primary documentation anchors.
- If a language-specific parser is unavailable, generate a conservative map from paths and recognizable declarations, then ask the agent to refine after reading code.
