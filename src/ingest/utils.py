import hashlib
import os
import subprocess

from sqlalchemy import select

from src.environment import ENV
from src.utils import Logger

WORKSPACE_PATH = ENV.WORKSPACE_PATH
TNL_REPO_DIR = "tnl"
TNL_REPO_PATH = f"{WORKSPACE_PATH}/{TNL_REPO_DIR}"
TNL_REPO_URL = ENV.TNL_REPO_URL


def run_command(cmd, cwd=None, timeout=None, env=None):
    subprocess.run(cmd, check=True, cwd=cwd, timeout=timeout, env=env)


def git_clone_or_pull():
    if not os.path.isdir(TNL_REPO_PATH):
        Logger.info(">> Cloning TNL repository...")
        run_command(["git", "clone", TNL_REPO_URL, TNL_REPO_PATH], cwd=WORKSPACE_PATH)
        Logger.success(">> Repository cloned")
    else:
        Logger.info(">> Pulling latest changes...")
        run_command(["git", "pull"], cwd=TNL_REPO_PATH)
        Logger.success(">> Repository updated")


def get_git_commit_hash():
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=TNL_REPO_PATH,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def _write_tnl_env():
    def to_on_off(value: bool) -> str:
        return "ON" if value else "OFF"

    lines = [
        "BUILD_DIR=build",
        f"CMAKE_BUILD_TYPE={ENV.TNL_CMAKE_BUILD_TYPE}",
        f"TNL_USE_CUDA={to_on_off(ENV.TNL_USE_CUDA)}",
        f"TNL_USE_HIP={to_on_off(ENV.TNL_USE_HIP)}",
        f"TNL_USE_OPENMP={to_on_off(ENV.TNL_USE_OPENMP)}",
        f"TNL_USE_MPI={to_on_off(ENV.TNL_USE_MPI)}",
    ]
    with open(f"{TNL_REPO_PATH}/.env", "w") as f:
        f.write("\n".join(lines) + "\n")


def build_tnl():
    _write_tnl_env()
    # Strip our app-level TNL_* and CMAKE_* vars so they don't leak into cmake
    # via just's `set` command — just reads cmake config from the .env file we wrote
    clean_env = {
        k: v for k, v in os.environ.items() if not k.startswith(("TNL_", "CMAKE_"))
    }
    Logger.info(">> Configuring build...")
    run_command(["just", "configure"], cwd=TNL_REPO_PATH, env=clean_env)
    Logger.info(f">> Building target: {ENV.TNL_BUILD_TARGET}...")
    run_command(
        ["just", "build", ENV.TNL_BUILD_TARGET], cwd=TNL_REPO_PATH, env=clean_env
    )
    Logger.success(">> Build completed")


def compute_machine_hash(data: dict) -> str:
    raw = "|".join(
        [
            data.get("CPU model name", "unknown"),
            str(data.get("CPU cores", 0)),
            data.get("GPU name", "none"),
            str(data.get("GPU CUDA cores", 0)),
        ]
    )
    return hashlib.sha256(raw.encode()).hexdigest()


def compute_run_hash(
    commit_hash: str,
    machine_hash: str,
    run_started_at: str,
    benchmark_name: str,
) -> str:
    raw = f"{commit_hash}:{machine_hash}:{run_started_at}:{benchmark_name}"
    return hashlib.sha256(raw.encode()).hexdigest()


async def get_or_create(session, model, defaults=None, **kwargs):
    result = await session.execute(select(model).filter_by(**kwargs))
    instance = result.scalar_one_or_none()

    if instance:
        return instance

    params = {**kwargs}
    if defaults:
        params.update(defaults)

    instance = model(**params)
    session.add(instance)
    await session.flush()
    return instance
