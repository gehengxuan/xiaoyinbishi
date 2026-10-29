import contextlib
import copy
import io
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from scripts.evaluate import checks_for, main
from support import ROOT, ScriptedModel, citation, finish, read, run, search, variant


class EvaluationTests(unittest.TestCase):
    def test_equivalent_document_sets_are_allowed_but_other_documents_are_rejected(self):
        quote = "报销材料应在费用发生后 30 天内提交。"
        both = [citation("D01", quote=quote), citation("D02", quote=quote)]
        case = {"expected": {"status": "answered", "citation_id_sets": [["D01"], ["D02"], ["D01", "D02"]]}}
        with variant([("D02", "C01", quote)]) as kb:
            model = ScriptedModel([search("报销"), read("D01"), read("D02"), finish(citations=both)])
            result, trace = run("报销期限多久？", model=model, kb=kb)
            for selected in (["D01"], ["D02"], ["D01", "D02"]):
                candidate = copy.deepcopy(result)
                candidate["citations"] = [cite for cite in candidate["citations"] if cite["document_id"] in selected]
                checks = checks_for(case, candidate, trace, kb)
                self.assertTrue(next(item["passed"] for item in checks if item["name"] == "引用文档集合"))
            for invalid in ([], [{**result["citations"][0], "document_id": "D03"}]):
                candidate = copy.deepcopy(result)
                candidate["citations"] = invalid
                checks = checks_for(case, candidate, trace, kb)
                self.assertFalse(next(item["passed"] for item in checks if item["name"] == "引用文档集合"))

    def test_recheck_copies_immutable_records_without_model_calls(self):
        with TemporaryDirectory() as directory:
            destination = Path(directory) / "recheck"
            with patch("knowledge_agent.mock_model.OfflineMockModel.choose", side_effect=AssertionError("No model calls allowed")):
                with contextlib.redirect_stdout(io.StringIO()):
                    code = main(["--provider", "mock", "--recheck-from", str(ROOT / "examples/mock"), "--output-dir", str(destination)])
            self.assertEqual(code, 0)
            summary = json.loads((destination / "evaluation.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["evaluation_mode"], "record_recheck")
            self.assertEqual(summary["passed"], 11)
            for filename in ("output.json", "trace.json", "trace.md"):
                self.assertEqual((destination / "01-clear" / filename).read_bytes(), (ROOT / "examples/mock/01-clear" / filename).read_bytes())


if __name__ == "__main__":
    unittest.main()
