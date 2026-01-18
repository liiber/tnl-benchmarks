from src.models.benchmarks import BenchmarkMachine

async def insert_benchmark_machine(async_session ,machine_meta):
    machine = BenchmarkMachine(
        cpu_cache_sizes=machine_meta["CPU cache sizes (L1d, L1i, L2, L3) (kiB)"],
        cpu_cores=int(machine_meta["CPU cores"]),
        cpu_max_frequency=float(machine_meta["CPU max frequency (MHz)"]),
        cpu_model_name=machine_meta["CPU model name"].strip(),
        cpu_threads_per_core=int(machine_meta["CPU threads per core"]),
        gpu_cuda_cores=int(machine_meta["GPU CUDA cores"]),
        gpu_architecture=float(machine_meta["GPU architecture"]),
        cpu_clock_rate_mhz=float(machine_meta["GPU clock rate (MHz)"]),
        gpu_global_memory_gb=float(machine_meta["GPU global memory (GB)"]),
        gpu_memory_ecc_enabled=bool(int(machine_meta["GPU memory ECC enabled"])),
        gpu_memory_clock_rate_mhz=float(machine_meta["GPU memory clock rate (MHz)"]),
        gpu_name=machine_meta["GPU name"].strip(),
        openmp_enabled=machine_meta["OpenMP enabled"].lower() == "yes",
        openmp_threads=int(machine_meta["OpenMP threads"]),
        architecture=machine_meta["architecture"],
        host_name=machine_meta["host name"].strip(),
        system=machine_meta["system"].strip(),
        system_release=machine_meta["system release"].strip(),
    )
    async_session.add(machine)
    await async_session.commit()
    return machine
