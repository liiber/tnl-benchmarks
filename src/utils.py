from datetime import UTC, datetime


def utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class Logger:
    _GREEN = "\033[32m"
    _RED = "\033[31m"
    _YELLOW = "\033[33m"
    _CYAN = "\033[36m"
    _BOLD = "\033[1m"
    _RESET = "\033[0m"

    @staticmethod
    def success(msg: str) -> None:
        print(f"{Logger._GREEN}{msg}{Logger._RESET}")

    @staticmethod
    def error(msg: str) -> None:
        print(f"{Logger._RED}{msg}{Logger._RESET}")

    @staticmethod
    def warning(msg: str) -> None:
        print(f"{Logger._YELLOW}{msg}{Logger._RESET}")

    @staticmethod
    def info(msg: str) -> None:
        print(f"{Logger._CYAN}{msg}{Logger._RESET}")

    @staticmethod
    def bold(msg: str) -> None:
        print(f"{Logger._BOLD}{msg}{Logger._RESET}")
