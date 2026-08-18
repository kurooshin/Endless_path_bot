import shlex

from config import GAMES, AGENT_DIR
import ssh_exec


def get_game(game_id: str) -> dict:
    if game_id not in GAMES:
        raise ValueError(f"بازی '{game_id}' تعریف نشده")
    return GAMES[game_id]


async def service_action(game_id: str, action: str) -> str:
    """action: start | stop | restart"""
    game = get_game(game_id)
    cmd = f"sudo /usr/bin/systemctl {action} {shlex.quote(game['service'])}"
    code, out, err = await ssh_exec.run(cmd)
    if code == 0:
        return f"✅ {action} روی {game['label']} با موفقیت انجام شد."
    return f"⚠️ خطا:\n{(err or out).strip()[:800]}"


async def service_status(game_id: str) -> str:
    game = get_game(game_id)
    cmd = f"systemctl is-active {shlex.quote(game['service'])}"
    _, out, _ = await ssh_exec.run(cmd)
    state = out.strip()
    icon = "🟢" if state == "active" else "🔴"
    return f"{icon} {game['label']}: {state}"


async def tail_log(game_id: str, n: int = 15) -> str:
    game = get_game(game_id)
    cmd = f"tail -n {n} {shlex.quote(game['log_path'])}"
    code, out, err = await ssh_exec.run(cmd)
    if code != 0:
        return f"⚠️ خطا در خواندن لاگ:\n{err.strip()[:500]}"
    return out.strip() or "(لاگ خالیه)"


async def get_log_size(game_id: str) -> int:
    game = get_game(game_id)
    cmd = f"stat -c %s {shlex.quote(game['log_path'])} 2>/dev/null || echo 0"
    _, out, _ = await ssh_exec.run(cmd)
    try:
        return int(out.strip())
    except ValueError:
        return 0


async def read_log_from(game_id: str, pos: int) -> str:
    game = get_game(game_id)
    cmd = f"tail -c +{pos + 1} {shlex.quote(game['log_path'])}"
    code, out, _ = await ssh_exec.run(cmd)
    return out if code == 0 else ""


async def run_console_command(game_id: str, command: str) -> str:
    game = get_game(game_id)
    if not game.get("rcon_enabled"):
        return "⚠️ این بازی RCON فعال نداره."
    remote_cmd = f"python3 {AGENT_DIR}/rcon_cli.py {shlex.quote(command)}"
    code, out, err = await ssh_exec.run(remote_cmd)
    if code != 0:
        return f"⚠️ خطا:\n{err.strip()[:500]}"
    return out.strip() or "(بدون خروجی)"
