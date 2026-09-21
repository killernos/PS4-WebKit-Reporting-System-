#!/usr/bin/env python3
"""Minimal reference report API. For production, put behind HTTPS/reverse proxy."""
import json, os, re, secrets
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HOST = os.getenv("REPORT_HOST", "127.0.0.1")
PORT = int(os.getenv("REPORT_PORT", "8765"))
ROUTE = os.getenv("REPORT_ROUTE", "/api/community-report")
STORAGE = os.getenv("REPORT_STORAGE", "./reports")
MAX_BODY = int(os.getenv("REPORT_MAX_BODY", "262144"))
ALLOWED_ORIGIN = os.getenv("REPORT_ALLOWED_ORIGIN", "*")
os.makedirs(STORAGE, exist_ok=True)

def safe_id(value):
    return re.sub(r"[^A-Za-z0-9_.-]", "_", str(value))[:128]

class Handler(BaseHTTPRequestHandler):
    def headers_common(self):
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", ALLOWED_ORIGIN)
        self.send_header("Access-Control-Allow-Headers", "content-type")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")

    def reply(self, code, payload):
        body = json.dumps(payload).encode()
        self.send_response(code); self.headers_common()
        self.send_header("Content-Length", str(len(body))); self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204); self.headers_common(); self.end_headers()

    def do_POST(self):
        if self.path != ROUTE:
            return self.reply(404, {"ok":False,"error":"not-found"})
        try:
            length = int(self.headers.get("Content-Length","0"))
        except ValueError:
            return self.reply(400, {"ok":False,"error":"bad-content-length"})
        if length <= 0 or length > MAX_BODY:
            return self.reply(413, {"ok":False,"error":"invalid-size"})
        try:
            report = json.loads(self.rfile.read(length))
        except Exception:
            return self.reply(400, {"ok":False,"error":"invalid-json"})
        required = ("schema","reportId","sessionId","timestamp","platform","firmware","host","test","state","stability","diagnostics")
        if not isinstance(report, dict) or any(k not in report for k in required):
            return self.reply(400, {"ok":False,"error":"invalid-report"})
        if report.get("schema") != "ps4-community-report-1" or report.get("platform") != "PS4":
            return self.reply(400, {"ok":False,"error":"unsupported-schema"})
        submission = "SUBMIT-" + secrets.token_hex(6).upper()
        envelope = {
            "submissionId": submission,
            "receivedAt": datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),
            "report": report
        }
        path = os.path.join(STORAGE, safe_id(submission) + ".json")
        with open(path, "x", encoding="utf-8") as f:
            json.dump(envelope, f, indent=2, ensure_ascii=False)
        return self.reply(201, {"ok":True,"submissionId":submission})

if __name__ == "__main__":
    print("Listening on http://%s:%d%s" % (HOST, PORT, ROUTE))
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
