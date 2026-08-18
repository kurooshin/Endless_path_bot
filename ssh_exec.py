import base64
import asyncssh
from config import SSH_HOST, SSH_PORT, SSH_USER, SSH_PRIVATE_KEY_B64

_conn = None


async def get_connection():
    global _conn
    if _conn is None or _conn.is_closed():
        key_text = base64.b64decode(SSH_PRIVATE_KEY_B64).decode("utf-8")
        key = asyncssh.import_private_key(key_text)
        _conn = await asyncssh.connect(
            SSH_HOST,
            port=SSH_PORT,
            username=SSH_USER,
            client_keys=[key],
            known_hosts=None,  # ساده‌سازی شده؛ برای امنیت بیشتر می‌تونی host key رو pin کنی
        )
    return _conn


async def run(command: str, timeout: int = 20):
    """دستور رو روی VPS اجرا می‌کنه و (exit_code, stdout, stderr) برمی‌گردونه"""
    conn = await get_connection()
    result = await conn.run(command, check=False, timeout=timeout)
    return result.exit_status, result.stdout or "", result.stderr or ""
