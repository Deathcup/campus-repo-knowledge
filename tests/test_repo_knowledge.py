import importlib.util
import json
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
            "frontend/src/views/log/List.vue": "<template><main>日志列表</main></template>",
            "frontend/src/views/log/Detail.vue": "<template><main>日志详情</main></template>",
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
            backend_modules = list((arc / "systems/backend/modules").glob("*/overview.md"))
            self.assertTrue(backend_modules)
            self.assertFalse(any(p.parent.name == "test" for p in backend_modules))
            log_doc = next(p for p in backend_modules if p.parent.name == "log")
            text = log_doc.read_text(encoding="utf-8")
            self.assertIn("## 接口与实现详解", text)
            self.assertIn("## 业务用例与总体流程", text)
            self.assertIn("## 业务规则与关键分支", text)
            self.assertIn("## 数据模型与持久化", text)
            self.assertIn("## 事务、一致性与并发", text)
            self.assertIn("/eslog", text)
            self.assertIn("/eslog/query", text)
            self.assertIn("backend/src/main/java", text)
            self.assertIn("[interface-post-eslog-query.md](interface-post-eslog-query.md)", text)
            self.assertTrue((log_doc.parent / "business-rules.md").exists())
            self.assertTrue((log_doc.parent / "interface-post-eslog-query.md").exists())
            self.assertTrue((log_doc.parent / "development.md").exists())
            interface_text = (log_doc.parent / "interface-post-eslog-query.md").read_text(encoding="utf-8")
            self.assertIn("## 完整实现链路", interface_text)
            self.assertIn("## 关键业务逻辑与算法", interface_text)
            self.assertIn("## 数据读写与副作用", interface_text)

            frontend_doc = arc / "systems/frontend/modules/log/overview.md"
            frontend_text = frontend_doc.read_text(encoding="utf-8")
            self.assertIn("## 页面总体流程", frontend_text)
            self.assertIn("## View 与重要组件结构", frontend_text)
            self.assertIn("## 状态、数据与副作用", frontend_text)
            self.assertIn("## 用户交互与关键前端逻辑", frontend_text)
            self.assertIn("[page-list.md](page-list.md)", frontend_text)
            self.assertIn("[page-detail.md](page-detail.md)", frontend_text)
            self.assertTrue((frontend_doc.parent / "page-list.md").exists())
            self.assertTrue((frontend_doc.parent / "page-detail.md").exists())
            self.assertTrue((frontend_doc.parent / "components-and-state.md").exists())

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
            self.assertTrue(any("3\t模块开发手册\t.repo-knowledge/systems/backend/modules/log/overview.md" in line for line in lines))
            self.assertTrue(any("4\t模块内专题\t.repo-knowledge/systems/backend/modules/log/interface-post-eslog-query.md" in line for line in lines))
            self.assertIn("5\t源码核验", lines[-1])

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

    def test_doctor_rejects_unresearched_templates_even_without_strict_flag(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            self.make_repo(repo)
            rk.command_init(SimpleNamespace(repo=str(repo)))
            nested = repo / ".repo-knowledge/features/example/notes.md"
            nested.parent.mkdir(parents=True, exist_ok=True)
            nested.write_text("# 记录\n\nTBD\n", encoding="utf-8")
            output = StringIO()
            with self.assertRaises(SystemExit), redirect_stdout(output):
                rk.command_doctor(SimpleNamespace(repo=str(repo), strict=False))
            report = output.getvalue()
            self.assertIn("含禁止残留", report)
            self.assertIn(".repo-knowledge/features/example/notes.md", report)
            self.assertIn("缺少至少一条可执行的编号业务流程", report)

    def test_upgrade_layout_moves_flat_module_into_own_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            flat = repo / ".repo-knowledge/systems/backend/modules/logs.md"
            flat.parent.mkdir(parents=True, exist_ok=True)
            flat.write_text("# 日志模块\n", encoding="utf-8")
            rk.command_upgrade_layout(SimpleNamespace(repo=str(repo)))
            self.assertFalse(flat.exists())
            self.assertEqual(
                "# 日志模块\n",
                (repo / ".repo-knowledge/systems/backend/modules/logs/overview.md").read_text(encoding="utf-8"),
            )

    def test_technical_layer_classes_converge_on_one_business_module(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            paths = [
                root / "src/main/java/com/acme/mapper/EmployeeMapper.java",
                root / "src/main/java/com/acme/service/impl/EmployeeServiceImpl.java",
                root / "src/main/java/com/acme/controller/EmployeeController.java",
                root / "src/test/java/com/acme/service/EmployeeServiceTest.java",
            ]
            self.assertEqual(
                {"Employee"},
                {rk.guess_module(path, root) for path in paths},
            )

    def test_module_map_merges_mechanical_candidates_into_business_capability(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            arc = root / ".repo-knowledge"
            (arc / "inventory").mkdir(parents=True)
            scan = {
                "systems": {
                    "backend": {
                        "modules": {
                            "Employee": [{"path": "EmployeeController.java", "routes": [], "endpoints": []}],
                            "Employeeec": [{"path": "EmployeeEcController.java", "routes": [], "endpoints": []}],
                        }
                    }
                }
            }
            (arc / "inventory/module-map.json").write_text(
                json.dumps({
                    "systems": {
                        "backend": {
                            "Employee": "employee-lifecycle",
                            "Employeeec": "employee-lifecycle",
                        }
                    }
                }),
                encoding="utf-8",
            )
            mapped = rk.apply_module_map(scan, arc)
            self.assertEqual(
                ["employee-lifecycle"],
                list(mapped["systems"]["backend"]["modules"]),
            )
            self.assertEqual(
                2,
                len(mapped["systems"]["backend"]["modules"]["employee-lifecycle"]),
            )


if __name__ == "__main__":
    unittest.main()
