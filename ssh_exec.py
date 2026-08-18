import asyncio
import base64
import asyncssh
from config import SSH_HOST, SSH_PORT, SSH_USER, SSH_PRIVATE_KEY_B64

_conn = None


async def get_connection():
    global _conn
    if _conn is None or _conn.is_closed():
        key_text = base64.b64decode(SSH_PRIVATE_KEY_B64).decode("utf-8")
        key = asyncssh.import_private_key(key_text)
        _conn = await asyncio.wait_for(
            asyncssh.connect(
                SSH_HOST,
                port=SSH_PORT,
                username=SSH_USER,
                client_keys=[key],
                known_hosts=None,
            ),
            timeout=15,
        )
    return _conn


async def run(command: str, timeout: int = 20):
    """دستور رو روی VPS اجرا می‌کنه و (exit_code, stdout, stderr) برمی‌گردونه"""
    global _conn
    try:
        conn = await get_connection()
        result = await asyncio.wait_for(
            conn.run(command, check=False, timeout=timeout), timeout=timeout + 5
        )
        return result.exit_status, result.stdout or "", result.stderr or ""
    except (asyncio.TimeoutError, asyncssh.Error, OSError) as e:
        _conn = None  # اتصال خراب رو دور بریز تا دفعه بعد از نو وصل بشه
        return 1, "", f"خطای اتصال SSH: {e}"
