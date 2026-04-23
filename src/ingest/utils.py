import os
import subprocess
import hashlib
from src.environment import ENV
from sqlalchemy import select

WORKSPACE_PATH="/workspace"
TNL_REPO_DIR="tnl"
TNL_REPO_PATH=f"{WORKSPACE_PATH}/{TNL_REPO_DIR}"
TNL_REPO_URL = ENV.TNL_REPO_URL

def run_command(cmd, cwd=None):
    subprocess.run(cmd, check=True, cwd=cwd)

def git_clone_or_pull():
    if not os.path.isdir(TNL_REPO_PATH):
        print(">> Repository does not exist")
        run_command(["git", "clone", TNL_REPO_URL, TNL_REPO_PATH], cwd=WORKSPACE_PATH)
        print(">> Repository cloned")
    else:
        print(">> Pulling existing repository")
        run_command(["git", "pull"], cwd=TNL_REPO_PATH)
        print(">> Repository pulled")

def get_git_commit_hash():
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=TNL_REPO_PATH,
        capture_output=True,
        text=True,
        check=True
    )
    return result.stdout.strip()

def build_tnl():
    # Note: The commands are used from the TNL Docs.
    #       Check https://tnl-project.gitlab.io/tnl/index.html for more
    run_command(["cmake", "-B", "build", "-S", ".", "-G", "Ninja"], cwd=TNL_REPO_PATH)
    run_command(["cmake", "--build", "build", "--target", "benchmarks"], cwd=TNL_REPO_PATH)

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def sha256_folder(folder_path):
    hashes = []
    for root, dirs, files in os.walk(folder_path):
        for file in sorted(files):
            full_path = os.path.join(root, file)
            with open(full_path, "rb") as f:
                h = hashlib.sha256()
                for chunk in iter(lambda: f.read(8192), b""):
                    h.update(chunk)
                hashes.append(h.hexdigest())

    return hashlib.sha256("".join(hashes).encode()).hexdigest()

def compute_machine_hash(data: dict) -> str:
    raw = "|".join([
        data.get("CPU model name", "unknown"),
        str(data.get("CPU cores", 0)),
        data.get("GPU name", "none"),
        str(data.get("GPU CUDA cores", 0)),
    ])
    return hashlib.sha256(raw.encode()).hexdigest()

def compute_run_hash(commit_hash: str, machine_hash: str) -> str:
    raw = f"{commit_hash}:{machine_hash}"
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