"""Python function that turns the explanation into spoken audio (English, Hindi, Marathi)."""
from http.server import BaseHTTPRequestHandler
import base64
import io
import json

LANGS = {"English": "en", "Hindi": "hi", "Marathi": "mr"}


def make_audio(text, language):
    from gtts import gTTS  # imported here so a missing package gives a clean error
    buf = io.BytesIO()
    gTTS(text=text[:1200], lang=LANGS.get(language, "en"), tld="co.in").write_to_fp(buf)
    return base64.b64encode(buf.getvalue()).decode()


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            size = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(size) or b"{}")
            text = str(body.get("text", "")).strip()
            if len(text) < 5:
                raise ValueError("no text")
            out, code = {"audio": make_audio(text, body.get("language", "English"))}, 200
        except Exception:
            out, code = {"error": "Could not make audio"}, 502
        data = json.dumps(out).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)
