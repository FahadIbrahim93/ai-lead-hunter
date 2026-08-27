#!/usr/bin/env python3
"""
AI Lead Hunter — Visual Dashboard
A zero-dependency local web server that shows your lead pipeline in the browser.

Run:  python dashboard.py
Then open:  http://localhost:8765
"""

import json
import subprocess
import sys
import webbrowser
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
ARTIFACTS = ROOT / "artifacts"
ENGINE = ROOT / "engine.py"
UI_FILE = ROOT / "ui.html"
PORT = 8765


def read_json_dir(folder: Path) -> list:
    """Read every .json file in a folder, sorted by filename."""
    if not folder.exists():
        return []
    items = []
    for f in sorted(folder.glob("*.json")):
        try:
            items.append(json.loads(f.read_text(encoding="utf-8")))
        except Exception:
            continue
    return items


def read_text_dir(folder: Path, ext: str = ".md") -> list:
    """Read every text file in a folder as {name, content}."""
    if not folder.exists():
        return []
    items = []
    for f in sorted(folder.glob(f"*{ext}")):
        try:
            items.append({"name": f.stem, "content": f.read_text(encoding="utf-8")})
        except Exception:
            continue
    return items


def build_state() -> dict:
    leads = read_json_dir(DATA / "leads")
    evidence = read_json_dir(DATA / "evidence")
    activity = read_json_dir(DATA / "activity")
    outreach = read_json_dir(DATA / "outreach")
    demos = read_text_dir(ARTIFACTS / "demos", ".md")

    clients = [l for l in leads if l.get("lead_type") != "internal_venture"]
    ventures = [l for l in leads if l.get("lead_type") == "internal_venture"]
    qualified = sum(1 for l in clients if l.get("lifecycle_status") == "QUALIFIED")
    tier_a = sum(1 for l in clients if l.get("tier") == "A")
    verified = sum(1 for l in clients if l.get("verified"))
    pending = sum(1 for o in outreach if o.get("status") == "pending_approval")

    # Sort leads by score desc
    clients.sort(key=lambda l: l.get("score", 0), reverse=True)
    ventures.sort(key=lambda l: l.get("score", 0), reverse=True)
    # Sort activity newest first by activity_id desc
    activity.sort(key=lambda a: a.get("activity_id", ""), reverse=True)

    return {
        "stats": {
            "leads": len(leads),
            "clients": len(clients),
            "ventures": len(ventures),
            "qualified": qualified,
            "tier_a": tier_a,
            "verified": verified,
            "evidence": len(evidence),
            "activity": len(activity),
            "outreach": len(outreach),
            "pending_approval": pending,
            "demos": len(demos),
        },
        "leads": clients,
        "ventures": ventures,
        "outreach": outreach,
        "activity": activity[:60],  # cap for UI speed
        "demos": demos,
    }


def run_engine(args: list) -> dict:
    """Run engine.py with the given args and capture output."""
    try:
        result = subprocess.run(
            [sys.executable, str(ENGINE)] + args,
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=120,
        )
        return {
            "ok": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
        }
    except Exception as e:
        return {"ok": False, "stdout": "", "stderr": str(e), "returncode": -1}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # silence request logs

    def _send(self, code: int, body: bytes, ctype: str):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path in ("/", "/index.html"):
            html = UI_FILE.read_text(encoding="utf-8")
            self._send(200, html.encode("utf-8"), "text/html; charset=utf-8")
            return

        if path == "/api/state":
            state = build_state()
            self._send(200, json.dumps(state).encode("utf-8"), "application/json")
            return

        self._send(404, b"Not found", "text/plain")

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path != "/api/action":
            self._send(404, b"Not found", "text/plain")
            return

        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length)
        try:
            body = json.loads(raw.decode("utf-8"))
        except Exception:
            self._send(400, b"Bad JSON", "text/plain")
            return

        action = body.get("action", "")
        lead_id = body.get("lead_id", "")

        if action == "audit":
            result = run_engine(["audit", lead_id])
        elif action == "demo":
            result = run_engine(["demo", lead_id])
        elif action == "demo-live":
            result = run_engine(["demo-live", lead_id])
        elif action == "outreach":
            result = run_engine(["outreach", lead_id])
        elif action == "discover":
            result = run_engine(["discover"])
        elif action == "ingest":
            result = run_engine(["ingest"])
        elif action == "verify-all":
            result = run_engine(["verify-all"])
        elif action == "verify":
            result = run_engine(["verify", lead_id])
        elif action == "validate":
            result = run_engine(["validate"])
        elif action == "status":
            result = run_engine(["status"])
        else:
            result = {"ok": False, "stdout": "", "stderr": f"Unknown action: {action}", "returncode": -1}

        self._send(200, json.dumps(result).encode("utf-8"), "application/json")


def main():
    print("=" * 60)
    print("  AI Lead Hunter — Dashboard")
    print("=" * 60)
    print(f"  Starting server at http://localhost:{PORT}")
    print("  Opening your browser...")
    print("  (Close this window to stop the server)")
    print("=" * 60)

    # Open browser after a short delay so the server is ready
    import threading
    threading.Timer(0.8, lambda: webbrowser.open(f"http://localhost:{PORT}")).start()

    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.server_close()


if __name__ == "__main__":
    main()
