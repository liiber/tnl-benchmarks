import os

import pytest


@pytest.fixture(autouse=True, scope="session")
def set_test_env():
    os.environ.setdefault("DB_USER", "test")
    os.environ.setdefault("DB_PASSWORD", "test")
    os.environ.setdefault("DB_NAME", "test")
    os.environ.setdefault("DB_HOST", "localhost")
    os.environ.setdefault("TNL_REPO_URL", "https://example.com/tnl.git")
    os.environ.setdefault("TNL_BENCHMARK_TIMEOUT_SECONDS", "")
