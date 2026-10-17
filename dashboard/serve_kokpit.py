"""Lightweight read-only kokpit HTTP server (stdlib)."""
from __future__ import annotations

import argparse
import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from contracts.models import ConstitutionRules
from core.user_rules import apply_user_request
from dashboard.analytics import build_analytics
from dashboard.snapshot import build_kokpit_snapshot, resolve_db_path

ROOT = Path(__file__).resolve().parents[1]
STATIC = Path(__file__).resolve().parent / "kokpit"
WEB_DIST = ROOT / "web" / "dist"
DEFAULT_DB = "data/golge.db"


def _json_response(handler: BaseHTTPRequestHandler, status: int, payload: dict) -> None:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    try:
        handler.wfile.write(body)
    except (BrokenPipeError, ConnectionResetError):
        pass  # The React poll was cancelled by navigation or a mode change.


class KokpitHandler(BaseHTTPRequestHandler):
    server_version = "GolgeKokpit/1.0"

    def log_message(self, fmt: str, *args) -> None:
        return

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/snapshot":
            qs = parse_qs(parsed.query)
            db_q = qs.get("db", [DEFAULT_DB])[0]
            if db_q.startswith("/") or ".." in db_q:
                _json_response(self, 400, {"error": "Invalid db path"})
                return
            try:
                resolve_db_path(db_q)
                snap = build_kokpit_snapshot(db_q)
                _json_response(self, 200, snap)
            except FileNotFoundError as exc:
                _json_response(self, 404, {"error": str(exc)})
            except (ValueError, SystemExit) as exc:
                _json_response(self, 400, {"error": str(exc)})
            return

        if path == "/api/analytics":
            qs = parse_qs(parsed.query)
            db_q = qs.get("db", [DEFAULT_DB])[0]
            if db_q.startswith("/") or ".." in db_q:
                _json_response(self, 400, {"error": "Invalid db path"})
                return
            try:
                resolve_db_path(db_q)
                payload = build_analytics(
                    db_q, hours=int(qs.get("hours", ["3"])[0]),
                    bucket_minutes=int(qs.get("bucket", ["10"])[0]),
                    limit=int(qs.get("limit", ["200"])[0]),
                )
                _json_response(self, 200, payload)
            except FileNotFoundError as exc:
                _json_response(self, 404, {"error": str(exc)})
            except (ValueError, SystemExit) as exc:
                _json_response(self, 400, {"error": str(exc)})
            return

        static = getattr(self.server, "static_dir", WEB_DIST)
        if path == "/" or path == "/index.html":
            self._serve_file(static / "index.html")
            return

        if path.startswith("/assets/"):
            rel = path.removeprefix("/assets/")
            target = (static / rel).resolve()
            if not target.is_relative_to(static.resolve()):
                self.send_error(403)
                return
            if target.is_file():
                self._serve_file(target)
                return

        self.send_error(404)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/api/simulate-rule":
            self.send_error(404)
            return

        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            data = json.loads(raw.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            _json_response(self, 400, {"error": "Invalid JSON"})
            return

        text = str(data.get("text", "")).strip()
        rules = ConstitutionRules()
        eff, label, msg = apply_user_request(rules, text)
        _json_response(
            self,
            200,
            {
                "user_request": label,
                "message": msg,
                "effective": {
                    "max_position_fraction_pct": float(eff.max_position_fraction * 100),
                    "max_spread_fraction_pct": float(eff.max_spread_fraction * 100),
                },
            },
        )

    def _serve_file(self, path: Path) -> None:
        data = path.read_bytes()
        ctype, _ = mimetypes.guess_type(str(path))
        if ctype is None:
            ctype = "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        if ctype and (
            ctype.startswith("text/html")
            or ctype.startswith("text/css")
            or "javascript" in ctype
        ):
            self.send_header("Cache-Control", "no-store")
        self.end_headers()
        try:
            self.wfile.write(data)
        except (BrokenPipeError, ConnectionResetError):
            pass  # Client disconnected before the response completed.


def main() -> None:
    parser = argparse.ArgumentParser(description="Gölge Defter kokpit (read-only)")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8501)
    parser.add_argument("--ui", choices=("web", "classic"), default="web",
                        help="web: React frontend; classic: previous HTML cockpit")
    args = parser.parse_args()

    static = WEB_DIST if args.ui == "web" else STATIC
    if not (static / "index.html").is_file():
        raise SystemExit(f"Missing UI build: {static}. Run: cd web && npm ci && npm run build")

    httpd = ThreadingHTTPServer((args.host, args.port), KokpitHandler)
    httpd.static_dir = static
    print(f"Kokpit http://{args.host}:{args.port}  ui={args.ui}  db={DEFAULT_DB}  (read-only)")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()


if __name__ == "__main__":
    main()
