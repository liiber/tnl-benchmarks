from src.ingest.mappers import build_machine_fields

CPU_METADATA = {
    "CPU model name": "Intel Core i7-9700K",
    "CPU cores": "8",
    "CPU max frequency (MHz)": "3600",
    "CPU threads per core": "1",
    "CPU cache sizes (L1d, L1i, L2, L3) (kiB)": "256, 256, 2048, 12288",
    "GPU name": "N/A",
    "GPU CUDA cores": "N/A",
    "OpenMP enabled": "yes",
    "OpenMP threads": "8",
    "host name": "gp7",
    "system": "Linux",
    "system release": "5.15.0",
    "architecture": "x86_64",
}


class TestBuildMachineFields:
    def test_maps_cpu_fields(self):
        fields = build_machine_fields(CPU_METADATA)
        assert fields["cpu_model_name"] == "Intel Core i7-9700K"
        assert fields["cpu_cores"] == 8
        assert fields["cpu_max_frequency"] == 3600
        assert fields["cpu_threads_per_core"] == 1

    def test_maps_system_fields(self):
        fields = build_machine_fields(CPU_METADATA)
        assert fields["host_name"] == "gp7"
        assert fields["system"] == "Linux"
        assert fields["system_release"] == "5.15.0"
        assert fields["architecture"] == "x86_64"

    def test_openmp_enabled_parsed_as_bool(self):
        assert build_machine_fields(CPU_METADATA)["openmp_enabled"] is True
        assert build_machine_fields({"OpenMP enabled": "no"})["openmp_enabled"] is False
        assert build_machine_fields({})["openmp_enabled"] is False

    def test_na_gpu_fields_normalized_to_none(self):
        fields = build_machine_fields(CPU_METADATA)
        assert fields["gpu_name"] is None
        assert fields["gpu_cuda_cores"] is None

    def test_required_numeric_fields_default_to_zero_when_absent(self):
        fields = build_machine_fields({})
        assert fields["cpu_cores"] == 0
        assert fields["cpu_max_frequency"] == 0
        assert fields["cpu_threads_per_core"] == 0
        assert fields["openmp_threads"] == 0

    def test_returns_all_model_columns(self):
        fields = build_machine_fields(CPU_METADATA)
        expected = {
            "cpu_cache_sizes",
            "cpu_cores",
            "cpu_max_frequency",
            "cpu_model_name",
            "cpu_threads_per_core",
            "gpu_name",
            "gpu_cuda_cores",
            "gpu_architecture",
            "gpu_clock_rate_mhz",
            "gpu_global_memory_gb",
            "gpu_memory_ecc_enabled",
            "gpu_memory_clock_rate_mhz",
            "openmp_enabled",
            "openmp_threads",
            "architecture",
            "host_name",
            "system",
            "system_release",
        }
        assert set(fields) == expected
