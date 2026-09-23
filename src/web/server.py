"""Small standard-library HTTP server for the local simulator web UI."""
from __future__ import annotations

from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
from pathlib import Path
from typing import Type
from urllib.parse import urlparse

from src.data import Dataset, load_dataset
from .api import catalogue_payload, score_payload

STATIC_DIR = Path(__file__).with_name("static")


def make_handler(dataset: Dataset, static_dir: Path = STATIC_DIR) -> Type[BaseHTTPRequestHandler]:
    """Create a request handler bound to one validated dataset."""

    class SimulatorHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802 - HTTP method name is framework-defined
            path = urlparse(self.path).path
            if path == "/api/catalogue":
                self._send_json(HTTPStatus.OK, catalogue_payload(dataset))
                return
            self._serve_static("index.html" if path == "/" else path.lstrip("/"))

        def do_POST(self) -> None:  # noqa: N802 - HTTP method name is framework-defined
            if urlparse(self.path).path != "/api/score":
                self._send_json(HTTPStatus.NOT_FOUND, {"error": "Маршрут не найден."})
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if length > 100_000:
                    raise ValueError("Слишком большой запрос.")
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
                if not isinstance(payload, dict):
                    raise ValueError("Тело запроса должно быть JSON-объектом.")
                self._send_json(HTTPStatus.OK, score_payload(payload, dataset))
            except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(error)})

        def _serve_static(self, relative_path: str) -> None:
            candidate = (static_dir / relative_path).resolve()
            try:
                candidate.relative_to(static_dir.resolve())
            except ValueError:
                self._send_json(HTTPStatus.NOT_FOUND, {"error": "Файл не найден."})
                return
            if not candidate.is_file():
                self._send_json(HTTPStatus.NOT_FOUND, {"error": "Файл не найден."})
                return
            content_type = mimetypes.guess_type(candidate.name)[0] or "application/octet-stream"
            data = candidate.read_bytes()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", f"{content_type}; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _send_json(self, status: HTTPStatus, payload: object) -> None:
            data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, format: str, *args: object) -> None:
            """Keep normal browser requests quiet; errors still get responses."""

    return SimulatorHandler


def run(host: str = "127.0.0.1", port: int = 8000) -> None:
    """Serve the local UI until interrupted with Ctrl+C."""
    server = ThreadingHTTPServer((host, port), make_handler(load_dataset()))
    print(f"Симулятор открыт: http://{host}:{port}")
    print("Нажмите Ctrl+C, чтобы остановить сервер.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nСервер остановлен.")
    finally:
        server.server_close()
