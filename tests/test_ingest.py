import json
from pathlib import Path

import src.ingest.ingest as ing


def _make_output(dir_path: Path, name: str) -> None:
    (dir_path / name).write_text("")  # fake benchmark binary
    (dir_path / f"{name}.log").write_text(
        json.dumps({"operation": "x", "time": "1.0", "loops": "1"})
    )
    (dir_path / f"{name}.metadata.json").write_text("{}")


class TestRunBenchmarks:
    def test_no_execute_collects_without_running(self, tmp_path, monkeypatch):
        _make_output(tmp_path, "tnl-benchmark-foo")
        monkeypatch.setattr(ing, "TNL_BENCHMARKS_BUILD_OUTPUT_DIR", str(tmp_path))
        calls = []
        monkeypatch.setattr(ing, "run_command", lambda *a, **k: calls.append(a))

        results = ing.run_benchmarks(execute=False)

        assert "tnl-benchmark-foo" in results
        assert calls == []  # binaries must NOT be executed in no-rebuild mode

    def test_execute_runs_binaries(self, tmp_path, monkeypatch):
        _make_output(tmp_path, "tnl-benchmark-foo")
        monkeypatch.setattr(ing, "TNL_BENCHMARKS_BUILD_OUTPUT_DIR", str(tmp_path))
        calls = []
        monkeypatch.setattr(ing, "run_command", lambda *a, **k: calls.append(a))

        results = ing.run_benchmarks(execute=True)

        assert "tnl-benchmark-foo" in results
        assert len(calls) == 1  # binary executed exactly once
