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
            log_doc = next(p for p in backend_modules if p.stem == "log")
            text = log_doc.read_text(encoding="utf-8")
            self.assertIn("## 接口与实现详解", text)
            self.assertIn("/eslog", text)
            self.assertIn("/eslog/query", text)
            self.assertIn("backend/src/main/java", text)

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
            self.assertTrue(any("3\t模块文档\t.repo-knowledge/systems/backend/modules/log.md" in line for line in lines))
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


if __name__ == "__main__":
    unittest.main()
