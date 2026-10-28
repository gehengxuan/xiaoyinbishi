"""Run unittest and save genuine test output under examples/."""

import argparse
import io
import platform
import sys
import time
import unittest
from pathlib import Path

from knowledge_agent.agent import utc_now
from knowledge_agent.recording import write_json


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path("examples"))
    args = parser.parse_args()
    stream = io.StringIO()
    started = time.monotonic()
    suite = unittest.defaultTestLoader.discover("tests")
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    log = stream.getvalue()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "test-results.txt").write_text(log, encoding="utf-8")
    write_json(args.output_dir / "test-results.json", {
        "generated_at": utc_now(), "python": platform.python_version(),
        "command": "PYTHONPATH=src python3 scripts/test.py",
        "tests_run": result.testsRun, "failures": len(result.failures),
        "errors": len(result.errors), "skipped": len(result.skipped),
        "duration_seconds": round(time.monotonic() - started, 3),
        "successful": result.wasSuccessful(),
        "boundary": "包含确定性 Mock、运行时校验和本机假 HTTP 服务的接口测试；不包含真实模型效果验收。",
    })
    print(log, end="")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
