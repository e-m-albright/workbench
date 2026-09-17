"""Opt-in real macOS probes: use a disposable prepared home, never host credentials."""

import contextlib
import http.server
import json
import os
import pty
import re
import select
import shlex
import signal
import socket
import subprocess
import termios
import threading
import time
from pathlib import Path

import pytest

PILOT = os.environ.get("WORKBENCH_NATIVE_CANARY_HOME")
pytestmark = pytest.mark.skipif(not PILOT, reason="requires an explicit disposable native pilot")


@pytest.fixture(scope="module", autouse=True)
def shared_harness():
    """Exercise actual harness loading and deny probes with synthetic host data."""
    from workbench.native_config import install_harness

    assert PILOT and Path(PILOT).resolve().is_relative_to("/private/tmp")
    home = Path(PILOT)
    pi = home / ".pi/agent"
    extensions = pi / "extensions"
    extensions.mkdir(parents=True, exist_ok=True)
    source = Path(__file__).resolve().parents[1] / "agents/pi/extensions"
    for name in ("footer.ts", "welcome.ts"):
        (extensions / name).write_text((source / name).read_text())
    (pi / "AGENTS.md").write_text("Synthetic shared global instructions.\n")
    (pi / "settings.json").write_text(
        json.dumps(
            {
                "defaultProvider": "openai",
                "defaultModel": "gpt-4.1",
                "tuiMode": "fullscreen",
            }
        )
    )
    policy = home / ".config/workbench/private-paths"
    policy.write_text(policy.read_text() + "\n~/.pi/agent/extensions/private/**\n")
    for relative in (
        "private-data",
        ".codex/history.jsonl",
        ".pi/agent/sessions/private.jsonl",
        ".config/connector/token.json",
        ".pi/agent/extensions/private/sentinel",
    ):
        path = home / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("synthetic-private-sentinel")
    (extensions / "boundary-canary.ts").write_text("""
import { readFileSync, writeFileSync } from "node:fs";
export default function(pi) {
  pi.on("session_start", async (_event, ctx) => {
    const root = process.env.WORKBENCH_HOST_HOME;
    for (const relative of [
      "private-data", ".codex/history.jsonl", ".pi/agent/sessions/private.jsonl",
      ".config/connector/token.json", ".pi/agent/extensions/private/sentinel"
    ]) {
      let denied = false;
      try { readFileSync(`${root}/${relative}`, "utf8"); } catch { denied = true; }
      if (!denied) throw new Error(`PRIVATE READ ALLOWED: ${relative}`);
    }
    let denied = false;
    try { writeFileSync(`${root}/.pi/agent/extensions/forbidden.ts`, "bad"); }
    catch { denied = true; }
    if (!denied) throw new Error("HOST HARNESS WRITE ALLOWED");
    ctx.ui.notify("BOUNDARY-CANARY-PASS", "info");
  });
}
""")
    install_harness(home)


def launch(repo, vendor, *args, stdin=None):
    assert PILOT
    assert Path(PILOT).resolve().is_relative_to("/private/tmp"), "Use a disposable pilot home"
    launcher = Path(PILOT) / ".local/share/workbench/shell/native-sandbox.py"
    return subprocess.run(
        ["/usr/bin/python3", "-I", "-S", str(launcher), vendor, "hosted", *args],
        cwd=repo,
        env={"HOME": PILOT, "PATH": "/usr/bin:/bin", "SYNTHETIC_SECRET": "not-in-child"},
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
        input=stdin,
    )


def test_real_files_network_and_children(tmp_path, monkeypatch):
    repo = tmp_path / "project"
    repo.mkdir()
    subprocess.run(["/usr/bin/git", "init", "--quiet", str(repo)], check=True)
    (repo / "public").write_text("released-canary")
    (repo / ".env").write_text("synthetic-only")
    (repo / "nested").mkdir()
    (repo / "nested/.env.production").write_text("nested-synthetic")
    private = tmp_path / "private"
    private.write_text("outside-canary")
    (repo / "escape").symlink_to(private)
    probe = Path(__file__).parent / "fixtures/native-probe.c"
    subprocess.run(["/usr/bin/clang", str(probe), "-o", str(repo / "probe")], check=True)
    hits = []

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            hits.append(self.path)
            self.send_response(200)
            self.end_headers()

        def log_message(self, *_args):
            pass

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    sockpath = repo / "host.sock"
    monkeypatch.chdir(repo)
    with contextlib.closing(socket.socket(socket.AF_UNIX)) as unix:
        unix.bind(sockpath.name)
        unix.listen()
        script = f"""
set -eu
denied() {{ if "$@" >/dev/null 2>&1; then echo "UNEXPECTED SUCCESS: $1"; exit 21; fi; }}
test -z "${{SYNTHETIC_SECRET:-}}"
test "$(/bin/cat public)" = released-canary
echo edited > edited
/bin/bash -c '/bin/cat public >/dev/null'
/usr/bin/python3 -I -S -c 'print("PYTHON-PASS")'
/usr/bin/git status --short >/dev/null
git status --short >/dev/null
./probe "$PPID"
denied /bin/cat {shlex.quote(str(private))}
denied /bin/cat escape
denied /bin/cat .env
denied /bin/bash -c 'echo overwritten > .env'
denied /bin/bash -c 'echo appended >> .env'
denied /bin/cat nested/.env.production
denied /bin/bash -c 'echo bad > nested/.env.production'
denied /bin/bash -c 'echo bad > nested/.env.future'
denied /bin/bash -c {shlex.quote("echo bad > " + shlex.quote(str(private)))}
denied /usr/bin/curl --noproxy '*' --max-time 2 -fsS http://127.0.0.1:{server.server_port}
denied /usr/bin/curl --max-time 2 -fsS http://localhost:{server.server_port}
denied /usr/bin/curl --unix-socket {shlex.quote(sockpath.name)} --noproxy '*' --max-time 2 -fsS http://localhost
/usr/bin/curl --max-time 10 -fsS https://example.com >/dev/null
echo CANARY-PASS
"""
        try:
            result = launch(repo, "shell", "-c", script)
            unix.settimeout(0.05)
            with pytest.raises(socket.timeout):
                unix.accept()
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=3)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "CANARY-PASS" in result.stdout
    assert private.read_text() == "outside-canary"
    assert (repo / ".env").read_text() == "synthetic-only"
    assert (repo / "nested/.env.production").read_text() == "nested-synthetic"
    assert not (repo / "nested/.env.future").exists()
    assert (repo / "edited").read_text() == "edited\n"
    assert not hits


@pytest.mark.parametrize("vendor", ["codex", "claude", "pi"])
def test_real_vendor_startup_without_credentials(tmp_path, vendor):
    (tmp_path / ".git").mkdir()
    result = launch(tmp_path, vendor, "--version")
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.strip()


def test_real_terminal_modes_work_but_input_injection_is_denied(tmp_path):
    (tmp_path / ".git").mkdir()
    source = tmp_path / "terminal.c"
    source.write_text("""#include <sys/ioctl.h>
#include <termios.h>
#include <stdio.h>
#include <errno.h>
int main(void) {
    struct termios old, raw;
    if (tcgetattr(0, &old)) return 2;
    raw = old; cfmakeraw(&raw);
    if (tcsetattr(0, TCSANOW, &raw)) { perror("raw mode"); return 3; }
    tcsetattr(0, TCSANOW, &old);
    char synthetic = 'x'; errno = 0;
    if (ioctl(0, TIOCSTI, &synthetic) == 0 || errno != EPERM) return 4;
    puts("TERMINAL-PASS"); return 0;
}
""")
    subprocess.run(["/usr/bin/clang", str(source), "-o", str(tmp_path / "terminal")], check=True)
    master, slave = pty.openpty()
    try:
        assert PILOT
        runner = Path(PILOT) / ".local/share/workbench/shell/native-sandbox.py"
        result = subprocess.run(
            ["/usr/bin/python3", "-I", "-S", str(runner), "shell", "hosted", "-c", "./terminal"],
            cwd=tmp_path,
            env={"HOME": PILOT, "PATH": "/usr/bin:/bin"},
            stdin=slave,
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert "TERMINAL-PASS" in result.stdout
    finally:
        os.close(master)
        os.close(slave)


@pytest.fixture
def synthetic_auth_store():
    assert PILOT and Path(PILOT).resolve().is_relative_to("/private/tmp")
    store = Path(PILOT) / ".local/share/workbench/model-auth"
    files = [store / "codex/auth.json", store / "pi/auth.json", store / "claude/.credentials.json"]
    assert not any(path.exists() for path in files), "Pilot must not contain existing credentials"
    try:
        yield store
    finally:
        for path in files:
            path.unlink(missing_ok=True)


def test_real_codex_shared_login_survives_a_second_repository(tmp_path, synthetic_auth_store):
    first, second = tmp_path / "first", tmp_path / "second"
    for repo in (first, second):
        (repo / ".git").mkdir(parents=True)
    result = launch(first, "codex", "login", "--with-api-key", stdin="synthetic-not-a-real-key\n")
    assert result.returncode == 0, result.stderr
    result = launch(second, "codex", "login", "status")
    assert result.returncode == 0, result.stderr
    assert "API key" in result.stderr + result.stdout
    assert (synthetic_auth_store / "codex/auth.json").is_file()


def test_real_claude_recognizes_only_the_shared_model_login(tmp_path, synthetic_auth_store):
    (tmp_path / ".git").mkdir()
    credential = synthetic_auth_store / "claude/.credentials.json"
    credential.write_text(
        json.dumps(
            {
                "claudeAiOauth": {
                    "accessToken": "synthetic-not-a-real-token",
                    "refreshToken": "synthetic-refresh",
                    "expiresAt": 4102444800000,
                    "scopes": ["user:inference"],
                }
            }
        )
    )
    credential.chmod(0o600)
    result = launch(tmp_path, "claude", "auth", "status", "--json")
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout)["loggedIn"] is True


def test_real_pi_rpc_starts_with_shared_auth_and_no_model_request(tmp_path, synthetic_auth_store):
    (tmp_path / ".git").mkdir()
    credential = synthetic_auth_store / "pi/auth.json"
    credential.write_text(json.dumps({"openai": {"type": "api_key", "key": "synthetic"}}))
    credential.chmod(0o600)
    result = launch(
        tmp_path,
        "pi",
        "--offline",
        "--provider",
        "openai",
        "--model",
        "gpt-4.1",
        "--mode",
        "rpc",
        stdin='{"type":"get_state"}\n',
    )
    assert result.returncode == 0, result.stderr
    rows = [json.loads(line) for line in result.stdout.splitlines() if line.startswith("{")]
    assert any(row.get("command") == "get_state" and row.get("success") for row in rows)
    assert not (synthetic_auth_store / "pi/settings.json").exists()


@pytest.mark.parametrize("width", [80, 120])
def test_real_pi_interactive_startup_has_footer_not_banner(tmp_path, synthetic_auth_store, width):
    """Exercise normal UI startup, not the version/RPC paths that skip trust storage."""
    (tmp_path / ".git").mkdir()
    (tmp_path / ".pi").mkdir()
    (tmp_path / ".pi/settings.json").write_text("{}")
    credential = synthetic_auth_store / "pi/auth.json"
    credential.write_text("{}")
    credential.chmod(0o600)
    master, slave = pty.openpty()
    termios.tcsetwinsize(slave, (30, width))
    assert PILOT
    runner = Path(PILOT) / ".local/share/workbench/shell/native-sandbox.py"
    process = subprocess.Popen(
        [
            "/usr/bin/python3",
            "-I",
            "-S",
            str(runner),
            "pi",
            "hosted",
            "--offline",
            "--provider",
            "openai",
            "--model",
            "gpt-4.1",
        ],
        cwd=tmp_path,
        env={"HOME": PILOT, "PATH": "/usr/bin:/bin", "TERM": "xterm-256color"},
        stdin=slave,
        stdout=slave,
        stderr=slave,
        start_new_session=True,
    )
    os.close(slave)
    output = b""
    try:
        deadline = time.monotonic() + 15
        declined = False
        while time.monotonic() < deadline:
            if select.select([master], [], [], 0.1)[0]:
                try:
                    output += os.read(master, 65536)
                except OSError:
                    break
            if not declined and b"trust" in output.lower() and b"EPERM" not in output:
                os.write(master, b"\x1b")
                declined = True
            plain = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", output.decode(errors="replace"))
            if "hosted > restricted" in plain or process.poll() is not None:
                break
        text = output.decode(errors="replace")
        assert "EPERM" not in text, text
        assert "hosted > restricted" in plain, text
        assert "ctx " in plain, text
        assert "Workbench managed" in plain, text
        assert "BOUNDARY-CANARY-PASS" in plain, text
        assert "openai/gpt-4.1" in plain, text
        assert "PI · NATIVE RESTRICTED" not in text
        assert process.poll() is None, text
        assert not (synthetic_auth_store / "pi/trust.json").exists()
        assert not (synthetic_auth_store / "pi/settings.json").exists()
    finally:
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=2)
        os.close(master)
