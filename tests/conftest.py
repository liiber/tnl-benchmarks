import os

# Set at import time, not in a fixture: `src.environment` builds its settings
# object on import, which happens while pytest collects the test modules —
# before any fixture runs.
os.environ.setdefault("DB_USER", "test")
os.environ.setdefault("DB_PASSWORD", "test")
os.environ.setdefault("DB_NAME", "test")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("TNL_REPO_URL", "https://example.com/tnl.git")
os.environ.setdefault("TNL_BENCHMARK_TIMEOUT_SECONDS", "")
