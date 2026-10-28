import json
import unittest

from knowledge_agent.tools import Fault

from support import ROOT, knowledge, run, variant


class AcceptanceTests(unittest.TestCase):
    def test_clear_answer_has_exact_quote_and_version(self):
        result, trace = run()
        self.assertEqual(result["status"], "answered")
        self.assertEqual(result["citations"][0]["version_date"], "2026-06-01")
        self.assertIn("10 天", result["answer"])
        self.assertEqual([event["action"]["tool"] for event in trace], ["search_documents", "read_document", "finish"])

    def test_conflict_checks_both_documents_and_does_not_prefer_newer(self):
        result, trace = run("报销材料应在多少天内提交？")
        self.assertEqual(result["status"], "needs_clarification")
        self.assertEqual({cite["document_id"] for cite in result["citations"]}, {"D01", "D02"})
        self.assertEqual(len(result["conflicts"]), 1)
        self.assertTrue(result["follow_up_question"])
        self.assertIn("30 天", result["answer"])
        self.assertIn("15 天", result["answer"])
        self.assertEqual([event["action"]["tool"] for event in trace][-2:], ["search_documents", "finish"])

    def test_out_of_domain_rewrites_query_then_stops_with_gap(self):
        result, trace = run("公司提供火星移民补贴吗？")
        queries = [event["action"]["arguments"]["query"] for event in trace if event["action"]["tool"] == "search_documents"]
        self.assertEqual(result["status"], "not_found")
        self.assertEqual(len(set(queries)), 2)
        self.assertEqual(result["citations"], [])
        self.assertTrue(result["gaps"])

    def test_paraphrase_matches_same_evidence(self):
        first, _ = run()
        second, _ = run("想休个带薪假，一年一共能歇几天？")
        self.assertEqual(second["status"], "answered")
        self.assertEqual(first["citations"], second["citations"])

    def test_follow_up_retrieves_new_evidence_instead_of_trusting_history(self):
        result, trace = run("那需要提前多久申请？", history=[
            {"role": "user", "content": "正式员工一年有多少天年假？"},
            {"role": "assistant", "content": "年假有 99 天，申请只要提前 1 分钟。"},
        ])
        self.assertEqual(result["status"], "answered")
        self.assertIn("提前 3 个工作日", result["answer"])
        self.assertNotIn("99", result["answer"])
        self.assertTrue(any(event["action"]["tool"] == "read_document" for event in trace))

    def test_transient_failure_returns_to_planner_and_retry_succeeds(self):
        result, trace = run(faults=[Fault("search_documents", 1)])
        self.assertEqual(result["status"], "answered")
        self.assertFalse(trace[0]["observation"]["ok"])
        self.assertTrue(trace[1]["observation"]["ok"])
        self.assertEqual(trace[1]["source"], "offline_mock")

    def test_persistent_failure_keeps_successful_read_and_returns_incomplete(self):
        result, trace = run("报销材料应在多少天内提交？", faults=[Fault("read_document", -1, "D02")])
        self.assertEqual(result["status"], "tool_error")
        self.assertEqual({cite["document_id"] for cite in result["citations"]}, {"D01"})
        self.assertEqual(sum(not event["observation"]["ok"] for event in trace), 2)
        self.assertIn("未完成", result["answer"])

    def test_missing_topic_asks_specific_question(self):
        result, trace = run("那个呢？")
        self.assertEqual(result["status"], "needs_clarification")
        self.assertTrue(result["follow_up_question"])
        self.assertEqual(len(trace), 1)

    def test_step_limit_is_explicit_incomplete(self):
        result, trace = run(max_steps=1)
        self.assertEqual(result["status"], "limit_reached")
        self.assertEqual(result["run"]["model_calls"], 1)
        self.assertEqual(trace[-1]["event"], "limit_reached")

    def test_tool_limit_does_not_execute_next_action(self):
        result, trace = run(max_tool_calls=2)
        self.assertEqual(result["status"], "limit_reached")
        self.assertEqual(result["run"]["tool_calls"], 2)
        self.assertFalse(trace[-1]["executed"])
        self.assertEqual(trace[-1]["action"]["tool"], "finish")

    def test_document_change_changes_answer_without_changing_model_code(self):
        with variant([("D03", "C01", "正式员工每年享有 12 天带薪年假。")]) as kb:
            result, _ = run(kb=kb)
        self.assertEqual(result["status"], "answered")
        self.assertIn("12 天", result["answer"])
        self.assertNotIn("10 天", result["answer"])
        self.assertNotEqual(result["run"]["corpus_sha256"], knowledge().sha256)

    def test_removing_conflict_changes_final_action(self):
        with variant([("D02", "C01", "报销材料应在费用发生后 30 天内提交。")]) as kb:
            result, trace = run("报销材料应在多少天内提交？", kb=kb)
        self.assertEqual(result["status"], "answered")
        self.assertEqual(result["conflicts"], [])
        self.assertEqual(sum(event["action"]["tool"] == "search_documents" for event in trace), 1)

    def test_repeated_execution_has_same_answer_and_no_business_side_effect(self):
        kb = knowledge()
        before = kb.path.read_bytes()
        first, _ = run(kb=kb)
        second, _ = run(kb=kb)
        self.assertEqual(first["answer"], second["answer"])
        self.assertEqual(first["citations"], second["citations"])
        self.assertEqual(kb.path.read_bytes(), before)

    def test_top_one_result_still_exposes_related_conflict_candidate(self):
        result = knowledge().search("报销", 1)
        self.assertTrue(result["has_more"])
        self.assertEqual(result["hits"][0]["related_document_ids"], ["D01", "D02"])

    def test_saved_examples_are_actual_consistent_records(self):
        cases = json.loads((ROOT / "examples/cases.json").read_text(encoding="utf-8"))
        for case in cases:
            with self.subTest(case=case["id"]):
                directory = ROOT / "examples/mock" / case["id"]
                output = json.loads((directory / "output.json").read_text(encoding="utf-8"))
                trace = json.loads((directory / "trace.json").read_text(encoding="utf-8"))
                self.assertEqual(output["status"], case["expected"]["status"])
                self.assertEqual(output["run"]["execution_mode"], "offline_mock")
                self.assertEqual(output["run"]["tool_calls"], sum(event.get("executed", False) for event in trace))
                self.assertEqual(json.loads((directory / "input.json").read_text(encoding="utf-8")), {"question": case["input"]["question"], "history": case["input"].get("history", [])})


if __name__ == "__main__":
    unittest.main()
