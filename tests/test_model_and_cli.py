import contextlib
import copy
import io
import json
import os
import ssl
import subprocess
import sys
import threading
import unittest
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from knowledge_agent.config import environment
from knowledge_agent.model import DeepSeekModel, OpenAICompatibleModel
from knowledge_agent.tools import TOOL_SCHEMAS
from knowledge_agent.types import ModelError, ModelProtocolError

from support import ROOT, ScriptedModel, finish, knowledge, read, search
from knowledge_agent.agent import Agent
from knowledge_agent.tools import ToolExecutor
from knowledge_agent.types import Request


def response_for(action, call_id="api_test_call"):
    return {
        "id": "test-http-response", "model": "deepseek-test-contract-only",
        "choices": [{"finish_reason": "tool_calls", "message": {
            "role": "assistant", "content": None,
            "reasoning_content": "DO_NOT_PERSIST_INTERNAL_REASONING",
            "tool_calls": [{"id": call_id, "type": "function", "function": {"name": action[0], "arguments": json.dumps(action[1], ensure_ascii=False)}}],
        }}],
        "usage": {"prompt_tokens": 12, "completion_tokens": 5, "total_tokens": 17},
    }


class ModelAdapterTests(unittest.TestCase):
    def test_deepseek_payload_matches_non_thinking_standard_endpoint(self):
        original = copy.deepcopy(TOOL_SCHEMAS)
        model = DeepSeekModel.from_env({"DEEPSEEK_API_KEY": "test-only-key"})
        payload = model.build_payload([], TOOL_SCHEMAS)
        self.assertEqual(model.endpoint, "https://api.deepseek.com/chat/completions")
        self.assertEqual(payload["thinking"], {"type": "disabled"})
        self.assertEqual(payload["tool_choice"], "required")
        self.assertIn("max_tokens", payload)
        self.assertNotIn("max_completion_tokens", payload)
        self.assertNotIn("parallel_tool_calls", payload)
        self.assertTrue(all("strict" not in tool["function"] for tool in payload["tools"]))
        self.assertEqual(TOOL_SCHEMAS, original)

    def test_openai_payload_uses_its_own_token_field(self):
        payload = OpenAICompatibleModel("test-only", "test-model").build_payload([], TOOL_SCHEMAS)
        self.assertIn("max_completion_tokens", payload)
        self.assertFalse(payload["parallel_tool_calls"])
        self.assertNotIn("thinking", payload)

    def test_parse_retains_public_usage_but_discards_internal_reasoning(self):
        action = DeepSeekModel.parse_response(response_for(search()))
        self.assertEqual(action.name, "search_documents")
        self.assertEqual(action.metadata["usage"]["total_tokens"], 17)
        self.assertNotIn("DO_NOT_PERSIST", json.dumps(action.assistant_message()) + json.dumps(action.metadata))

    def test_invalid_and_parallel_calls_are_rejected_without_partial_execution(self):
        valid = response_for(search())
        parallel = copy.deepcopy(valid)
        parallel["choices"][0]["message"]["tool_calls"] *= 2
        malformed = copy.deepcopy(valid)
        malformed["choices"][0]["message"]["tool_calls"][0]["function"]["arguments"] = "{bad"
        for value in (None, [], {}, {"choices": [None]}, parallel, malformed):
            with self.subTest(response=value):
                with self.assertRaises(ModelProtocolError):
                    DeepSeekModel.parse_response(value)

    def test_http_error_is_sanitized_and_not_retried(self):
        model = DeepSeekModel("private-test-key")
        failure = urllib.error.HTTPError("https://example.invalid/private-test-key", 401, "private-test-key", {}, io.BytesIO(b"private-test-key"))
        with patch("urllib.request.urlopen", side_effect=failure) as transport:
            with self.assertRaises(ModelError) as caught:
                model.choose([], TOOL_SCHEMAS)
        self.assertIn("401", str(caught.exception))
        self.assertNotIn("private-test-key", str(caught.exception))
        self.assertEqual(transport.call_count, 1)

    def test_config_error_does_not_echo_secret(self):
        with self.assertRaises(ValueError) as caught:
            DeepSeekModel.from_env({"DEEPSEEK_API_KEY": "test-only", "DEEPSEEK_BASE_URL": "https://user:private-test-key@example.invalid"})
        self.assertNotIn("private-test-key", str(caught.exception))

    def test_insufficient_balance_has_actionable_sanitized_error(self):
        model = DeepSeekModel("private-test-key")
        failure = urllib.error.HTTPError("https://example.invalid", 402, "private-test-key", {}, io.BytesIO(b"private-test-key"))
        with patch("urllib.request.urlopen", side_effect=failure) as transport:
            with self.assertRaises(ModelError) as caught:
                model.choose([], TOOL_SCHEMAS)
        self.assertIn("余额不足", str(caught.exception))
        self.assertNotIn("private-test-key", str(caught.exception))
        self.assertEqual(transport.call_count, 1)

    def test_tls_error_points_to_ca_configuration_without_echoing_details(self):
        failure = urllib.error.URLError(ssl.SSLCertVerificationError(1, "private-test-key"))
        with patch("urllib.request.urlopen", side_effect=failure):
            with self.assertRaises(ModelError) as caught:
                DeepSeekModel("private-test-key").choose([], TOOL_SCHEMAS)
        self.assertIn("SSL_CERT_FILE", str(caught.exception))
        self.assertNotIn("private-test-key", str(caught.exception))

    def test_missing_key_is_not_replaced_by_mock(self):
        with self.assertRaises(ValueError):
            DeepSeekModel.from_env({})

    def test_real_http_serialization_loop_with_fake_server_is_contract_test_only(self):
        # This uses urllib over localhost but is NOT a live LLM evaluation.
        payloads = []
        actions = [search(), read(), finish()]

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                payloads.append(payload)
                body = json.dumps(response_for(actions[len(payloads) - 1], f"http_call_{len(payloads)}"), ensure_ascii=False).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *args):
                pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            model = DeepSeekModel("local-test-only", base_url=f"http://127.0.0.1:{server.server_port}", timeout=2)
            local_opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
            with patch("urllib.request.urlopen", side_effect=local_opener.open):
                result, trace = Agent(model, ToolExecutor(knowledge())).run(Request("正式员工一年有多少天带薪年假？"))
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)
        self.assertEqual(result["status"], "answered")
        self.assertEqual(len(payloads), 3)
        self.assertEqual(payloads[1]["messages"][-1]["role"], "tool")
        self.assertIn('"hits"', payloads[1]["messages"][-1]["content"])
        self.assertIn("10 天", payloads[2]["messages"][-1]["content"])
        self.assertNotIn("DO_NOT_PERSIST_INTERNAL_REASONING", json.dumps(trace))


class ConfigurationAndCLITests(unittest.TestCase):
    def test_env_file_is_literal_and_does_not_execute_shell_syntax(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / ".env"
            path.write_text('DEEPSEEK_API_KEY="literal-$(do-not-execute)"\nDEEPSEEK_MODEL=test-model\n', encoding="utf-8")
            values = environment(path)
            self.assertEqual(values["DEEPSEEK_API_KEY"], "literal-$(do-not-execute)")

    def test_unknown_env_keys_are_rejected_without_echoing_values(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / ".env"
            path.write_text("UNKNOWN=private-test-key\n", encoding="utf-8")
            with self.assertRaises(ValueError) as caught:
                environment(path)
            self.assertNotIn("private-test-key", str(caught.exception))

    def _cli(self, *arguments):
        env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
        return subprocess.run([sys.executable, "-m", "knowledge_agent", *arguments], cwd=ROOT, env=env, capture_output=True, text=True, timeout=10)

    def test_cli_emits_parseable_json_and_separate_mock_warning_and_records(self):
        with TemporaryDirectory() as directory:
            completed = self._cli("--question", "正式员工一年有多少天带薪年假？", "--provider", "mock", "--output-dir", directory)
            self.assertEqual(completed.returncode, 0)
            self.assertEqual(json.loads(completed.stdout)["status"], "answered")
            self.assertIn("OFFLINE MOCK", completed.stderr)
            for name in ("input.json", "output.json", "trace.json", "trace.md", "run-config.json"):
                self.assertTrue((Path(directory) / name).is_file())

    def test_cli_nonzero_exit_code_for_incomplete_and_limit(self):
        with TemporaryDirectory() as directory:
            conflict = self._cli("--question", "报销期限多久？", "--output-dir", directory)
            limit = self._cli("--question", "年假多久？", "--max-steps", "1", "--output-dir", directory)
        self.assertEqual(conflict.returncode, 3)
        self.assertEqual(json.loads(conflict.stdout)["status"], "needs_clarification")
        self.assertEqual(limit.returncode, 5)

    def test_cli_rejects_empty_question(self):
        result = self._cli("--question", " ")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stderr)["status"], "invalid_input")


if __name__ == "__main__":
    unittest.main()
