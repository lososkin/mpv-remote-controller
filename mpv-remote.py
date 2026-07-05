#!/usr/bin/python3
import json
import mimetypes
import os
import socket
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

DEFAULT_SOCKET_PATH = "/tmp/mpvsocket"
DEFAULT_SERVER_ADDRESS = "0.0.0.0:8000"


def _parse_server_address(address):
    host, port = address.rsplit(":", 1)
    return host, int(port)


SOCKET_PATH = os.environ.get("SOCKET_PATH", DEFAULT_SOCKET_PATH)
SERVER_ADDRESS = _parse_server_address(
    os.environ.get("SERVER_ADDRESS", DEFAULT_SERVER_ADDRESS)
)
STATIC_DIR = Path(__file__).parent / "static"

STATIC_ROUTES = {
    "/": "index.html",
    "/subs": "subs.html",
    "/media": "media.html",
    "/styles.css": "styles.css",
    "/script.js": "script.js",
}

COMMAND_MAPPER = {
    "sub": ["osd-auto", "cycle", "sub"],
    "audio": ["osd-auto", "cycle", "audio"],
    "speed+": ["osd-auto", "add", "speed", "0.1"],
    "speed-": ["osd-auto", "add", "speed", "-0.1"],
    "-10s": ["osd-auto", "seek", "-10"],
    "+10s": ["osd-auto", "seek", "10"],
    "volumeup": ["osd-auto", "add", "volume", "5"],
    "volumedown": ["osd-auto", "add", "volume", "-5"],
    "-min": ["osd-auto", "seek", "-60"],
    "+min": ["osd-auto", "seek", "60"],
    "space": ["cycle", "pause"],
    "forward": ["osd-auto", "playlist-next"],
    "back": ["osd-auto", "playlist-prev"],
    "f": ["cycle", "fullscreen"],
}

SOCKET_ERROR_MSG = (
    "Socket file not found!\n"
    "1) Ensure mpv is running.\n"
    "2) Check input-ipc-server option in your mpv config.\n"
    "3) Check SOCKET_PATH env var or mpv-remote.py defaults"
)


def load_static_files():
    static_files = {}
    for path in STATIC_DIR.iterdir():
        if path.is_file():
            static_files[path.name] = path.read_bytes()
    return static_files


STATIC_FILES = load_static_files()


def send_mpv_ipc(command):
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
        sock.connect(SOCKET_PATH)
        payload = json.dumps({"command": command}, ensure_ascii=False) + "\n"
        sock.send(payload.encode("utf-8"))


def load_files_in_mpv(filenames):
    for index, filename in enumerate(filenames):
        mode = "replace" if index == 0 else "append"
        send_mpv_ipc(["loadfile", str(Path.cwd() / filename), mode])


def add_subtitle(filename):
    send_mpv_ipc(["sub-add", str(Path.cwd() / filename)])


def start_mpv(filenames):
    paths = [str(Path.cwd() / name) for name in filenames]
    subprocess.Popen(
        ["mpv", f"--input-ipc-server={SOCKET_PATH}", *paths],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


class HttpRequestHandler(BaseHTTPRequestHandler):
    def respond(self, code, content_type, data):
        self.send_response(code)
        self.send_header("content-type", content_type)
        self.end_headers()
        self.wfile.write(data)

    def respond_json(self, code, payload):
        self.respond(
            code,
            "application/json",
            json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        )

    def read_json_body(self):
        length = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(length))

    def serve_static(self, filename):
        data = STATIC_FILES.get(filename)
        if data is None:
            self.respond(404, "text/html", b"404")
            return
        content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
        self.respond(200, content_type, data)

    def handle_getdirs(self):
        entries = sorted(os.listdir())
        dirs = [name for name in entries if os.path.isdir(name)]
        files = [name for name in entries if os.path.isfile(name)]
        self.respond_json(200, {"dirs": dirs, "files": files})

    def handle_changedir(self):
        target = self.read_json_body()["dir"]
        path = Path.cwd() / target

        if path.is_dir():
            os.chdir(target)
            self.respond_json(200, {"type": "dir"})
            return

        try:
            add_subtitle(target)
        except (FileNotFoundError, ConnectionRefusedError, OSError):
            print(SOCKET_ERROR_MSG)
        self.respond_json(200, {"type": "file"})

    def handle_playnow(self):
        filenames = self.read_json_body()["files"]
        self.respond_json(200, {})

        try:
            load_files_in_mpv(filenames)
        except (FileNotFoundError, ConnectionRefusedError, OSError):
            threading.Thread(target=start_mpv, args=(filenames,), daemon=True).start()

    def handle_appendtoplaylist(self):
        filenames = self.read_json_body()["files"]
        try:
            for filename in filenames:
                send_mpv_ipc(["loadfile", str(Path.cwd() / filename), "append"])
        except (FileNotFoundError, ConnectionRefusedError, OSError):
            print(SOCKET_ERROR_MSG)
        self.respond_json(200, {})

    def handle_command(self):
        command_name = self.read_json_body()["command"]
        command = COMMAND_MAPPER.get(command_name)
        if command is None:
            self.respond(400, "application/json", b'{"error": "unknown command"}')
            return
        try:
            send_mpv_ipc(command)
        except (FileNotFoundError, ConnectionRefusedError, OSError):
            print(SOCKET_ERROR_MSG)
        self.respond_json(200, {})

    def do_GET(self):
        if self.path == "/getdirs/":
            self.handle_getdirs()
            return

        static_file = STATIC_ROUTES.get(self.path)
        if static_file:
            self.serve_static(static_file)
            return

        self.respond(404, "text/html", b"404")

    def do_POST(self):
        handlers = {
            "/changedir/": self.handle_changedir,
            "/playnow/": self.handle_playnow,
            "/appendtoplaylist/": self.handle_appendtoplaylist,
            "/command/": self.handle_command,
        }
        handler = handlers.get(self.path)
        if handler:
            handler()
            return
        self.respond(404, "text/html", b"404")


def print_local_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            print("IP in local network:", sock.getsockname()[0])
    except OSError:
        pass


def main():
    http_server = HTTPServer(SERVER_ADDRESS, HttpRequestHandler)
    host, port = SERVER_ADDRESS
    print(f"Starting mpv control server at http://{host}:{port}/")
    if host == "0.0.0.0":
        print_local_ip()
    print("Quit the mpv server with CONTROL-C.")
    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        http_server.server_close()
        print("\nMPV remote controller server stopped.")


if __name__ == "__main__":
    main()
