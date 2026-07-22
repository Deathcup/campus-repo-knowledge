import importlib.util
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from types import SimpleNamespace


SCRIPT = Path(__file__).parents[1] / "scripts" / "repo_knowledge.py"
SPEC = importlib.util.spec_from_file_location("repo_knowledge", SCRIPT)
rk = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(rk)


class RepoKnowledgeTests(unittest.TestCase):
    def make_repo(self, root: Path) -> None:
        files = {
            "backend/pom.xml": "<project/>",
            "backend/src/main/java/com/acme/log/EsLogController.java": '''
                @RequestMapping("/eslog")
                class EsLogController {
                    @PostMapping("/query")
                    public Page query(QueryRequest request) { return service.query(request); }
                }
            ''',
            "backend/src/main/java/com/acme/log/EsLogService.java": "class EsLogService { Page query() {} }",
            "backend/src/test/java/com/acme/log/EsLogServiceTest.java": "class EsLogServiceTest { void queryUsesTenantScope() {} }",
            "frontend/package.json": '{"scripts":{"test":"vitest"}}',
            "frontend/src/api/eslog.ts": "export const queryEsLog = () => client.post('/eslog/query')",
            "frontend/src/views/log/Search.vue": "<template><main>日志查询</main></template>",
        }
        for relative, content in files.items():
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")

    def test_init_creates_three_level_navigation_and_module_docs(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            self.make_repo(repo)
            rk.command_init(SimpleNamespace(repo=str(repo)))

            arc = repo / ".repo-knowledge"
            self.assertTrue((arc / "INDEX.md").exists())
            self.assertTrue((arc / "systems/backend/overview.md").exists())
            self.assertTrue((arc / "systems/frontend/overview.md").exists())
            backend_modules = list((arc / "systems/backend/modules").glob("*.md"))
            self.assertTrue(backend_modules)
            self.assertFalse(any(p.stem == "test" for p in backend_modules))
            log_doc = next(p for p in backend_modules if p.stem == "log")
            text = log_doc.read_text(encoding="utf-8")
            self.assertIn("## 接口与实现详解", text)
            self.assertIn("## 业务用例与总体流程", text)
            self.assertIn("## 业务规则与关键分支", text)
            self.assertIn("## 数据模型与持久化", text)
            self.assertIn("## 事务、一致性与并发", text)
            self.assertIn("/eslog", text)
            self.assertIn("/eslog/query", text)
            self.assertIn("backend/src/main/java", text)

            frontend_doc = arc / "systems/frontend/modules/log.md"
            frontend_text = frontend_doc.read_text(encoding="utf-8")
            self.assertIn("## 页面总体流程", frontend_text)
            self.assertIn("## View 与重要组件结构", frontend_text)
            self.assertIn("## 状态、数据与副作用", frontend_text)
            self.assertIn("## 用户交互与关键前端逻辑", frontend_text)

            navigation = (arc / "inventory/navigation.json").read_text(encoding="utf-8")
            self.assertIn('"kind": "frontend"', navigation)
            self.assertIn('"kind": "backend"', navigation)

    def test_context_outputs_ordered_route(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            self.make_repo(repo)
            rk.command_init(SimpleNamespace(repo=str(repo)))
            output = StringIO()
            with redirect_stdout(output):
                rk.command_context(SimpleNamespace(repo=str(repo), query="后端日志 eslog/query 接口", limit=2))
            lines = output.getvalue().splitlines()
            self.assertIn("1\t根总览", lines[0])
            self.assertTrue(any("2\t子系统总览\t.repo-knowledge/systems/backend/overview.md" in line for line in lines))
            self.assertTrue(any("3\t模块开发手册\t.repo-knowledge/systems/backend/modules/log.md" in line for line in lines))
            self.assertIn("4\t源码核验", lines[-1])

    def test_scan_does_not_overwrite_human_overviews(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            self.make_repo(repo)
            rk.command_init(SimpleNamespace(repo=str(repo)))
            index = repo / ".repo-knowledge/INDEX.md"
            overview = repo / ".repo-knowledge/systems/backend/overview.md"
            index.write_text("# 人工根总览\n", encoding="utf-8")
            overview.write_text("# 人工后端总览\n", encoding="utf-8")
            rk.command_scan(SimpleNamespace(repo=str(repo), update=True))
            self.assertEqual("# 人工根总览\n", index.read_text(encoding="utf-8"))
            self.assertEqual("# 人工后端总览\n", overview.read_text(encoding="utf-8"))

    def test_strict_doctor_rejects_unresearched_templates(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            self.make_repo(repo)
            rk.command_init(SimpleNamespace(repo=str(repo)))
            output = StringIO()
            with self.assertRaises(SystemExit), redirect_stdout(output):
                rk.command_doctor(SimpleNamespace(repo=str(repo), strict=True))
            report = output.getvalue()
            self.assertIn("模板提示或待调查内容", report)
            self.assertIn("缺少至少一条可执行的编号业务流程", report)


if __name__ == "__main__":
    unittest.main()
