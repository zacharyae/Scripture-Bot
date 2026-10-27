#!/usr/bin/env python3
"""Local AI chat: serves index.html, relays chat to Ollama, saves chats as JSON files.
Standard library only. Run:  python3 server.py
Settings (environment variables): CHAT_HOST, CHAT_PORT, OLLAMA_URL, CHAT_DIR
"""
import json
import os
import re
import shutil
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote
from urllib import error as er
from urllib import request as rq

HOST = os.environ.get("CHAT_HOST", "127.0.0.1")  # localhost only; reach it through an SSH tunnel
PORT = int(os.environ.get("CHAT_PORT", "8000"))
OLLAMA = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")
CHATS = Path(os.environ.get("CHAT_DIR", Path.home() / "ai-workspace" / "chats")).expanduser()
HERE = Path(__file__).resolve().parent
ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")  # chat ids can never contain slashes or dots
FILES = Path(os.environ.get("FILES_DIR", Path.home() / "ai-workspace" / "files")).expanduser()
SEG_RE = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_. +()\-]{0,100}$")  # no leading dots, no slashes
MAX_FILE = 2_000_000
CHATS.mkdir(parents=True, exist_ok=True)
FILES.mkdir(parents=True, exist_ok=True)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def reply(self, obj, status=200):
        data = json.dumps(obj).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def body(self):
        n = int(self.headers.get("Content-Length") or 0)
        if n > 20_000_000:
            raise ValueError("body too large")
        return json.loads(self.rfile.read(n) or b"{}")

    def chat_file(self):
        cid = self.path.split("?")[0].rsplit("/", 1)[-1]
        return CHATS / f"{cid}.json" if ID_RE.match(cid) else None

    def status(self):
        def get(path):
            try:
                with rq.urlopen(OLLAMA + path, timeout=3) as r:
                    return json.load(r)
            except Exception:
                return None

        ps, ver = get("/api/ps"), get("/api/version")
        loaded = None
        if ps is not None:
            loaded = []
            for m in ps.get("models", []):
                left = None
                try:
                    left = (datetime.fromisoformat(m["expires_at"]) - datetime.now(timezone.utc)).total_seconds()
                except Exception:
                    pass
                loaded.append({"name": m.get("name", "?"), "size": m.get("size", 0),
                               "vram": m.get("size_vram", 0), "left": left})
        mem = {}
        try:
            for line in open("/proc/meminfo"):
                k, v = line.split(":")
                mem[k] = int(v.split()[0]) * 1024
        except Exception:
            pass
        try:
            up = float(open("/proc/uptime").read().split()[0])
        except Exception:
            up = None
        du = shutil.disk_usage(CHATS)
        return {"up": ver is not None, "ollama": ver.get("version") if ver else None, "loaded": loaded,
                "cpu": os.getloadavg()[0], "cores": os.cpu_count(),
                "ram_total": mem.get("MemTotal"), "ram_avail": mem.get("MemAvailable"),
                "uptime": up, "disk_free": du.free, "chats": len(list(CHATS.glob("*.json")))}

    def file_path(self):
        """Map a URL to a path inside FILES, or None if it is unsafe."""
        rel = unquote(self.path.split("?")[0][len("/api/files/"):])
        parts = rel.split("/")
        if not rel or len(rel) > 200 or len(parts) > 5 or not all(SEG_RE.match(s) for s in parts):
            return None
        full = FILES.joinpath(*parts)
        try:
            full.resolve().relative_to(FILES.resolve())  # also blocks symlinks that point outside
        except ValueError:
            return None
        return full

    def backup(self, f, move=False):
        d = FILES / ".backups"
        d.mkdir(exist_ok=True)
        base = time.strftime("%Y%m%d-%H%M%S-") + f.relative_to(FILES).as_posix().replace("/", "__")
        dest, n = d / base, 1
        while dest.exists():  # never overwrite an earlier backup
            dest, n = d / f"{n}-{base}", n + 1
        (shutil.move if move else shutil.copy2)(f, dest)

    def list_files(self):
        out = []
        for f in FILES.rglob("*"):
            rel = f.relative_to(FILES)
            if f.is_file() and not any(s.startswith(".") for s in rel.parts):
                st = f.stat()
                out.append({"path": rel.as_posix(), "size": st.st_size, "mtime": st.st_mtime})
        out.sort(key=lambda x: x["mtime"], reverse=True)
        return out[:500]

    def put_file(self):
        f = self.file_path()
        if not f:
            return self.reply({"error": "Invalid file name. Use letters, numbers, dots and dashes, with up to 4 folders."}, 400)
        try:
            b = self.body()
            content = b.get("content", "")
            if not isinstance(content, str) or len(content.encode()) > MAX_FILE:
                return self.reply({"error": "File is too large (2 MB limit)."}, 400)
            if f.exists():
                if f.is_dir():
                    return self.reply({"error": "That name is a folder."}, 400)
                if not b.get("overwrite"):
                    return self.reply({"error": "exists"}, 409)
                self.backup(f)  # keep the old version
            f.parent.mkdir(parents=True, exist_ok=True)
            tmp = f.with_name(f.name + ".tmp")
            tmp.write_text(content, "utf-8")
            tmp.replace(f)
            self.reply({"ok": True, "path": f.relative_to(FILES).as_posix()})
        except Exception as e:
            self.reply({"error": str(e)}, 400)

    def delete_file(self):
        f = self.file_path()
        if f and f.is_file():
            self.backup(f, move=True)  # deleted files go to .backups, not away
        self.reply({"ok": True})

    def do_GET(self):
        p = self.path.split("?")[0]
        try:
            if p in ("/", "/index.html"):
                data = (HERE / "index.html").read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
            elif p == "/api/models":
                with rq.urlopen(OLLAMA + "/api/tags", timeout=5) as r:
                    tags = json.load(r)
                self.reply({"models": sorted(m["name"] for m in tags.get("models", []))})
            elif p == "/api/files":
                self.reply({"files": self.list_files()})
            elif p.startswith("/api/files/"):
                f = self.file_path()
                if f and f.is_file():
                    data = f.read_bytes()
                    self.send_response(200)
                    self.send_header("Content-Type", "application/octet-stream")  # always a download, never run in the page
                    self.send_header("Content-Disposition", 'attachment; filename="%s"' % f.name.replace('"', ""))
                    self.send_header("X-Content-Type-Options", "nosniff")
                    self.send_header("Content-Length", str(len(data)))
                    self.end_headers()
                    self.wfile.write(data)
                else:
                    self.reply({"error": "not found"}, 404)
            elif p == "/api/status":
                self.reply(self.status())
            elif p == "/api/chats":
                out = []
                for f in CHATS.glob("*.json"):
                    try:
                        c = json.loads(f.read_text("utf-8"))
                        out.append({"id": c["id"], "title": c.get("title", "Chat"), "updated": c.get("updated", 0)})
                    except Exception:
                        pass
                out.sort(key=lambda c: c["updated"], reverse=True)
                self.reply({"chats": out})
            elif p.startswith("/api/chats/"):
                f = self.chat_file()
                if f and f.exists():
                    self.reply(json.loads(f.read_text("utf-8")))
                else:
                    self.reply({"error": "not found"}, 404)
            else:
                self.reply({"error": "not found"}, 404)
        except FileNotFoundError:
            self.reply({"error": "index.html must be in the same folder as server.py"}, 500)
        except (er.URLError, OSError) as e:
            self.reply({"error": f"Can't reach Ollama at {OLLAMA}: {e}"}, 502)

    def do_PUT(self):
        if self.path.startswith("/api/files/"):
            return self.put_file()
        f = self.chat_file()
        if not f:
            return self.reply({"error": "bad chat id"}, 400)
        try:
            c = self.body()
            c = {
                "id": f.stem,
                "title": str(c.get("title", "Chat"))[:200],
                "model": str(c.get("model", "")),
                "updated": time.time(),
                "messages": c.get("messages", []),
            }
            tmp = f.with_suffix(".tmp")
            tmp.write_text(json.dumps(c, ensure_ascii=False, indent=1), "utf-8")
            tmp.replace(f)
            self.reply({"ok": True})
        except Exception as e:
            self.reply({"error": str(e)}, 400)

    def do_PATCH(self):  # rename a chat without touching its messages or its sort order
        f = self.chat_file()
        if not f or not f.exists():
            return self.reply({"error": "not found"}, 404)
        try:
            c = json.loads(f.read_text("utf-8"))
            c["title"] = str(self.body().get("title", c.get("title", "Chat")))[:200]
            tmp = f.with_suffix(".tmp")
            tmp.write_text(json.dumps(c, ensure_ascii=False, indent=1), "utf-8")
            tmp.replace(f)
            self.reply({"ok": True})
        except Exception as e:
            self.reply({"error": str(e)}, 400)

    def do_DELETE(self):
        if self.path.startswith("/api/files/"):
            return self.delete_file()
        f = self.chat_file()
        if f:
            f.unlink(missing_ok=True)
        self.reply({"ok": True})

    def do_POST(self):
        if self.path in ("/api/load", "/api/unload"):  # an empty generate call loads or unloads a model
            try:
                b = self.body()
                unload = self.path == "/api/unload"
                payload = {"model": b["model"], "keep_alive": 0 if unload else b.get("keep_alive", "30m")}
                if not unload and b.get("options"):
                    payload["options"] = b["options"]
                req = rq.Request(OLLAMA + "/api/generate", json.dumps(payload).encode(), {"Content-Type": "application/json"})
                with rq.urlopen(req, timeout=600) as r:
                    r.read()
                return self.reply({"ok": True})
            except er.HTTPError as e:
                return self.reply({"error": e.read().decode("utf-8", "replace")}, e.code)
            except Exception as e:
                return self.reply({"error": str(e)}, 502)
        if self.path != "/api/chat":
            return self.reply({"error": "not found"}, 404)
        try:
            b = self.body()
            payload = json.dumps({
                "model": b["model"],
                "messages": b["messages"],
                "stream": True,
                "options": b.get("options", {}),
                **({"keep_alive": b["keep_alive"]} if "keep_alive" in b else {}),
                **({"think": b["think"]} if "think" in b else {}),
            }).encode()
            resp = rq.urlopen(rq.Request(OLLAMA + "/api/chat", payload, {"Content-Type": "application/json"}), timeout=600)
        except er.HTTPError as e:
            msg = e.read().decode("utf-8", "replace")
            try:
                msg = json.loads(msg).get("error", msg)
            except Exception:
                pass
            return self.reply({"error": msg}, e.code)
        except Exception as e:
            return self.reply({"error": f"Can't reach Ollama: {e}"}, 502)
        self.send_response(200)
        self.send_header("Content-Type", "application/x-ndjson")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        try:
            for line in resp:  # stream Ollama's reply straight through
                self.wfile.write(line)
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass  # you pressed Stop or closed the tab
        finally:
            resp.close()  # closing this also stops Ollama generating


if __name__ == "__main__":
    print(f"Chat page: http://{HOST}:{PORT}   Ollama: {OLLAMA}   Chats saved in: {CHATS}")
    try:
        ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
    except KeyboardInterrupt:
        pass
