import json
from pathlib import Path

import pytest

from src.ingest.parsers import parse_log, parse_metadata

SAMPLE_LOG_ROWS = [
    {
        "operation": "copy (memcpy)",
        "precision": "double",
        "host allocator": "Host",
        "size": "100000",
        "performer": "CPU",
        "time": "4.022910e-05",
        "time_stddev": "6.588973e-06",
        "time_stddev/time": "1.637862e-01",
        "loops": "10",
        "bandwidth": "3.704075e+01",
        "speedup": "N/A",
    },
    {
        "operation": "copy (memcpy)",
        "precision": "double",
        "host allocator": "Host",
        "size": "100000",
        "performer": "GPU",
        "time": "6.995000e-06",
        "time_stddev": "3.389313e-07",
        "time_stddev/time": "4.845337e-02",
        "loops": "10",
        "bandwidth": "2.130259e+02",
        "speedup": "5.751122e+00",
    },
]

SAMPLE_METADATA = {
    "CPU model name": "Intel Core i7-9700K",
    "CPU cores": "8",
    "CPU max frequency (MHz)": "3600",
    "CPU threads per core": "1",
    "GPU name": "N/A",
    "GPU CUDA cores": "N/A",
    "OpenMP enabled": "yes",
    "OpenMP threads": "8",
    "host name": "gp7",
    "system": "Linux",
    "system release": "5.15.0",
    "architecture": "x86_64",
}


@pytest.fixture
def log_file(tmp_path: Path) -> Path:
    path = tmp_path / "tnl-benchmark-blas.log"
    path.write_text("\n".join(json.dumps(row) for row in SAMPLE_LOG_ROWS))
    return path


@pytest.fixture
def metadata_file(tmp_path: Path) -> Path:
    path = tmp_path / "tnl-benchmark-blas.metadata.json"
    path.write_text(json.dumps(SAMPLE_METADATA))
    return path


class TestParseLog:
    def test_returns_correct_row_count(self, log_file: Path):
        rows = parse_log(str(log_file))
        assert len(rows) == 2

    def test_parses_operation(self, log_file: Path):
        rows = parse_log(str(log_file))
        assert rows[0]["operation"] == "copy (memcpy)"

    def test_parses_time_as_float(self, log_file: Path):
        rows = parse_log(str(log_file))
        assert rows[0]["metrics"]["time"] == pytest.approx(4.02291e-05)

    def test_parses_bandwidth(self, log_file: Path):
        rows = parse_log(str(log_file))
        assert rows[0]["metrics"]["bandwidth"] == pytest.approx(37.04075)

    def test_loops_parsed_as_int(self, log_file: Path):
        rows = parse_log(str(log_file))
        assert rows[0]["metrics"]["loops"] == 10

    def test_dimension_fields_in_metadata(self, log_file: Path):
        rows = parse_log(str(log_file))
        assert rows[0]["metadata"]["precision"] == "double"
        assert rows[0]["metadata"]["host allocator"] == "Host"
        assert rows[0]["metadata"]["size"] == "100000"
        assert rows[0]["metadata"]["performer"] == "CPU"

    def test_skips_non_json_lines(self, tmp_path: Path):
        path = tmp_path / "mixed.log"
        path.write_text(
            "== Array operations ==\n"
            + json.dumps(SAMPLE_LOG_ROWS[0])
            + "\nsome other text\n"
            + json.dumps(SAMPLE_LOG_ROWS[1])
        )
        rows = parse_log(str(path))
        assert len(rows) == 2

    def test_new_stddev_field_name(self, tmp_path: Path):
        row = {**SAMPLE_LOG_ROWS[0], "time_stddev": "1.23e-06"}
        path = tmp_path / "new.log"
        path.write_text(json.dumps(row))
        rows = parse_log(str(path))
        assert rows[0]["metrics"]["stddev"] == pytest.approx(1.23e-06)

    def test_old_stddev_field_name_fallback(self, tmp_path: Path):
        row = {k: v for k, v in SAMPLE_LOG_ROWS[0].items() if k != "time_stddev"}
        row["stddev"] = "9.99e-07"
        path = tmp_path / "old.log"
        path.write_text(json.dumps(row))
        rows = parse_log(str(path))
        assert rows[0]["metrics"]["stddev"] == pytest.approx(9.99e-07)

    def test_no_operation_row_still_parsed(self, tmp_path: Path):
        row = {
            k: v
            for k, v in SAMPLE_LOG_ROWS[0].items()
            if k not in ("operation", "performer")
        }
        row["size"] = "1000"
        path = tmp_path / "no_op.log"
        path.write_text(json.dumps(row))
        rows = parse_log(str(path))
        assert len(rows) == 1
        assert rows[0]["operation"] is None
        assert rows[0]["metadata"]["size"] == "1000"


class TestParseMetadata:
    def test_returns_dict(self, metadata_file: Path):
        metadata = parse_metadata(str(metadata_file))
        assert isinstance(metadata, dict)

    def test_parses_cpu_model(self, metadata_file: Path):
        metadata = parse_metadata(str(metadata_file))
        assert metadata["CPU model name"] == "Intel Core i7-9700K"

    def test_parses_cpu_cores(self, metadata_file: Path):
        metadata = parse_metadata(str(metadata_file))
        assert metadata["CPU cores"] == "8"


# Real rows captured from the segments and sort benchmarks, whose logs name the
# operation field differently ("function" / only "performer") than blas ("operation").
SEGMENTS_ROW = {
    "segments setup": "constant",
    "segments type": "CSR",
    "function": "forElements",
    "performer": "sequential",
    "time": "1.081300e-06",
    "speedup": "N/A",
    "bandwidth": "9.470082e+08",
    "cycles_stddev/cycles": "3.622458e-02",
    "loops": "10",
}

SORT_ROW = {
    "size": "1048576",
    "distribution": "random",
    "value_type": "int",
    "device": "host",
    "performer": "STL sort",
    "time": "5.566514e-02",
    "cycles_stddev/cycles": "9.502397e-03",
    "loops": "10",
}


class TestOperationResolution:
    def _parse_one(self, tmp_path: Path, row: dict) -> dict:
        path = tmp_path / "one.log"
        path.write_text(json.dumps(row))
        return parse_log(str(path))[0]

    def test_operation_field_used_directly(self, tmp_path: Path):
        row = self._parse_one(tmp_path, SAMPLE_LOG_ROWS[0])
        assert row["operation"] == "copy (memcpy)"
        assert "operation" not in row["metadata"]
        assert row["metadata"]["performer"] == "CPU"

    def test_function_used_when_no_operation(self, tmp_path: Path):
        row = self._parse_one(tmp_path, SEGMENTS_ROW)
        assert row["operation"] == "forElements"
        assert "function" not in row["metadata"]
        assert row["metadata"]["performer"] == "sequential"
        assert row["metadata"]["segments type"] == "CSR"

    def test_performer_used_when_no_operation_or_function(self, tmp_path: Path):
        row = self._parse_one(tmp_path, SORT_ROW)
        assert row["operation"] == "STL sort"
        assert "performer" not in row["metadata"]
        assert row["metadata"]["device"] == "host"
        assert row["metadata"]["distribution"] == "random"

    def test_ratio_metrics_excluded_from_metadata(self, tmp_path: Path):
        row = self._parse_one(tmp_path, SEGMENTS_ROW)
        assert "cycles_stddev/cycles" not in row["metadata"]
        assert "speedup" not in row["metadata"]

    def test_row_without_operation_fields_yields_none(self, tmp_path: Path):
        row = self._parse_one(tmp_path, {"size": "10", "time": "1.0", "loops": "5"})
        assert row["operation"] is None
