from __future__ import annotations

import argparse
import socket
import sys
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import create_engine, text

from agent_core.llm_provider import get_llm_provider
from core.config import get_settings


def check_port(host: str, port: int, label: str) -> tuple[bool, str]:
    try:
        with socket.create_connection((host, port), timeout=3):
            return True, f"{label}: ok ({host}:{port})"
    except OSError as exc:
        return False, f"{label}: failed ({host}:{port}) - {exc}"


def check_health(url: str) -> tuple[bool, str]:
    try:
        with urlopen(url, timeout=5) as response:
            body = response.read().decode("utf-8", errors="ignore")
            return True, f"health endpoint: ok ({body})"
    except URLError as exc:
        return False, f"health endpoint: failed - {exc}"


def check_database(sync_url: str) -> tuple[bool, str]:
    try:
        engine = create_engine(sync_url)
        with engine.connect() as conn:
            tables = conn.execute(
                text(
                    """
                    SELECT tablename
                    FROM pg_tables
                    WHERE schemaname = 'public'
                    ORDER BY tablename
                    """
                )
            ).scalars().all()
        engine.dispose()
        if not tables:
            return False, "database: connected, but no public tables found"
        return True, f"database: ok ({len(tables)} tables)"
    except Exception as exc:
        return False, f"database: failed - {exc}"


async def check_llm() -> tuple[bool, str]:
    try:
        llm = get_llm_provider()
        response = await llm.chat(
            [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Reply with only API OK"},
            ]
        )
        ok = response.strip() == "API OK"
        return ok, f"llm: {'ok' if ok else 'unexpected response'} ({response})"
    except Exception as exc:
        return False, f"llm: failed - {exc}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Check whether the local backend environment is ready.")
    parser.add_argument("--check-llm", action="store_true", help="Ping the configured LLM provider as well.")
    args = parser.parse_args()

    settings = get_settings()
    checks: list[tuple[bool, str]] = []

    checks.append((sys.version_info >= (3, 11), f"python: {sys.version.split()[0]}"))
    checks.append(check_port("127.0.0.1", 5432, "postgres"))
    checks.append(check_port("127.0.0.1", 6379, "redis"))
    checks.append(check_port("127.0.0.1", 9000, "minio"))
    checks.append(check_health("http://127.0.0.1:8000/health"))
    checks.append(check_database(settings.DATABASE_SYNC_URL))

    if args.check_llm:
        import asyncio

        checks.append(asyncio.run(check_llm()))

    all_ok = True
    for ok, message in checks:
        prefix = "[OK]" if ok else "[FAIL]"
        print(f"{prefix} {message}")
        all_ok = all_ok and ok

    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
