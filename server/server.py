#!/usr/bin/env python3
"""Minimal reference report API. For production, put behind HTTPS/reverse proxy."""
import json, os, re, secrets
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from collections import Counter, defaultdict

HOST = os.getenv("REPORT_HOST", "127.0.0.1")
PORT = int(os.getenv("REPORT_PORT", "8765"))
ROUTE = os.getenv("REPORT_ROUTE", "/api/community-report")
STORAGE = os.getenv("REPORT_STORAGE", "./reports")
MAX_BODY = int(os.getenv("REPORT_MAX_BODY", "262144"))
ALLOWED_ORIGIN = os.getenv("REPORT_ALLOWED_ORIGIN", "*")
os.makedirs(STORAGE, exist_ok=True)

def safe_id(value):
    return re.sub(r"[^A-Za-z0-9_.-]", "_", str(value))[:128]

def load_reports():
    rows = []
    for name in os.listdir(STORAGE):
        if not name.endswith(".json"):
            continue
        try:
            with open(os.path.join(STORAGE, name), encoding="utf-8") as f:
                envelope = json.load(f)
            report = envelope.get("report", {})
            if isinstance(report, dict):
                rows.append(report)
        except Exception:
            pass
    return rows

def stage_analysis(reports):
    """Aggregate reached stages by firmware/build from explicit event history."""
    groups = defaultdict(list)
    for r in reports:
        fw = str((r.get("firmware") or {}).get("version", "UNKNOWN"))
        host = r.get("host") or {}
        build = str(host.get("buildId") or host.get("version") or "UNKNOWN")
        groups[(fw, build)].append(r)

    output = []
    for (fw, build), rows in sorted(groups.items()):
        counts = Counter()
        for r in rows:
            reached = set()
            for e in (r.get("events") or []):
                if isinstance(e, dict):
                    stage = e.get("stage") or e.get("name")
                    if stage:
                        reached.add(str(stage))
            last = (r.get("test") or {}).get("lastStage")
            if last:
                reached.add(str(last))
            for stage in reached:
                counts[stage] += 1
        n = len(rows)
        stages = {}
        for stage, count in sorted(counts.items()):
            stages[stage] = {"reached":count,"rate":round(count*100.0/n,2) if n else 0.0}
        output.append({"firmware":fw,"buildId":build,"sampleSize":n,"stages":stages})
    return output

def stage_comparisons(stage_rows, min_samples=10, warn_delta=10.0):
    by_fw = defaultdict(list)
    for row in stage_rows:
        by_fw[row["firmware"]].append(row)
    out = []
    for fw, rows in by_fw.items():
        rows.sort(key=lambda x:x["buildId"])
        for i in range(1,len(rows)):
            a,b=rows[i-1],rows[i]
            all_stages=sorted(set(a["stages"]) | set(b["stages"]))
            diffs=[]
            sufficient=a["sampleSize"]>=min_samples and b["sampleSize"]>=min_samples
            for stage in all_stages:
                ar=a["stages"].get(stage,{}).get("rate",0.0)
                br=b["stages"].get(stage,{}).get("rate",0.0)
                delta=round(br-ar,2)
                diffs.append({"stage":stage,"baselineRate":ar,"currentRate":br,"deltaPoints":delta,
                              "signal":bool(sufficient and delta <= -warn_delta)})
            out.append({"firmware":fw,"baselineBuild":a["buildId"],"currentBuild":b["buildId"],
                        "baselineSampleSize":a["sampleSize"],"currentSampleSize":b["sampleSize"],
                        "sufficientSample":sufficient,"stages":diffs})
    return out

def regression_analysis(reports, min_samples=10, warn_delta=10.0):
    """Compare build observations within each firmware.

    This is descriptive triage, not a causal test. Builds are ordered by first
    observed report timestamp when available, otherwise by build id.
    """
    groups = defaultdict(list)
    for r in reports:
        fw = str((r.get("firmware") or {}).get("version", "UNKNOWN"))
        host = r.get("host") or {}
        build = str(host.get("buildId") or host.get("version") or "UNKNOWN")
        groups[(fw, build)].append(r)

    summaries = {}
    for key, rows in groups.items():
        n = len(rows)
        successes = sum(1 for r in rows if (r.get("test") or {}).get("status") == "SUCCESS")
        timeouts = sum(1 for r in rows if (r.get("test") or {}).get("status") == "TIMEOUT" or (r.get("stability") or {}).get("timeout") is True)
        shutdowns = sum(1 for r in rows if (r.get("stability") or {}).get("consoleShutdown") is True)
        crashes = sum(1 for r in rows if (r.get("stability") or {}).get("browserCrash") is True)
        first = min([str(r.get("timestamp") or r.get("startedAt") or "") for r in rows] or [""])
        summaries[key] = {
            "sampleSize":n, "firstObserved":first,
            "successRate":round(successes*100.0/n,2) if n else 0,
            "timeoutRate":round(timeouts*100.0/n,2) if n else 0,
            "shutdownRate":round(shutdowns*100.0/n,2) if n else 0,
            "browserCrashRate":round(crashes*100.0/n,2) if n else 0
        }

    by_fw = defaultdict(list)
    for (fw, build), summary in summaries.items():
        by_fw[fw].append((build, summary))

    comparisons = []
    for fw, items in by_fw.items():
        items.sort(key=lambda x: (x[1]["firstObserved"], x[0]))
        for i in range(1, len(items)):
            base_build, base = items[i-1]
            new_build, new = items[i]
            metrics = {}
            for metric in ("successRate","timeoutRate","shutdownRate","browserCrashRate"):
                delta = round(new[metric] - base[metric], 2)
                metrics[metric] = {"baseline":base[metric],"current":new[metric],"deltaPoints":delta}
            sufficient = base["sampleSize"] >= min_samples and new["sampleSize"] >= min_samples
            signals = []
            if sufficient:
                if metrics["successRate"]["deltaPoints"] <= -warn_delta: signals.append("SUCCESS_RATE_DROP")
                if metrics["timeoutRate"]["deltaPoints"] >= warn_delta: signals.append("TIMEOUT_RATE_INCREASE")
                if metrics["shutdownRate"]["deltaPoints"] >= warn_delta: signals.append("SHUTDOWN_RATE_INCREASE")
                if metrics["browserCrashRate"]["deltaPoints"] >= warn_delta: signals.append("BROWSER_CRASH_RATE_INCREASE")
            comparisons.append({
                "firmware":fw, "baselineBuild":base_build, "currentBuild":new_build,
                "baselineSampleSize":base["sampleSize"], "currentSampleSize":new["sampleSize"],
                "sufficientSample":sufficient, "signals":signals, "metrics":metrics,
                "interpretation":"investigate" if signals else ("insufficient-sample" if not sufficient else "no-threshold-signal")
            })
    return comparisons

def build_stats():
    reports = load_reports()
    statuses = Counter()
    firmwares = Counter()
    stages = Counter()
    builds = Counter()
    stability = Counter()
    matrix = defaultdict(lambda: Counter())

    for r in reports:
        test = r.get("test") or {}
        fw = str((r.get("firmware") or {}).get("version", "UNKNOWN"))
        host = r.get("host") or {}
        build = str(host.get("buildId") or host.get("version") or "UNKNOWN")
        status = str(test.get("status", "UNKNOWN"))
        stage = str(test.get("lastStage", "UNKNOWN"))
        statuses[status] += 1
        firmwares[fw] += 1
        stages[stage] += 1
        builds[build] += 1
        matrix[(fw, build)][status] += 1
        for key, value in (r.get("stability") or {}).items():
            if value is True:
                stability[key] += 1

    comparisons = []
    for (fw, build), counts in sorted(matrix.items()):
        attempts = sum(counts.values())
        success = counts.get("SUCCESS", 0)
        comparisons.append({
            "firmware": fw, "buildId": build, "attempts": attempts,
            "success": success,
            "successRate": round((success / attempts * 100.0), 2) if attempts else 0.0,
            "statuses": dict(counts)
        })

    stage_rows = stage_analysis(reports)
    return {
        "ok": True,
        "sampleSize": len(reports),
        "statusCounts": dict(statuses),
        "firmwareCounts": dict(firmwares),
        "lastStageCounts": dict(stages.most_common()),
        "buildCounts": dict(builds),
        "stabilityObservations": dict(stability),
        "firmwareBuildComparison": comparisons,
        "regressionComparisons": regression_analysis(reports),
        "stageReach": stage_rows,
        "stageComparisons": stage_comparisons(stage_rows),
        "note": "Aggregates describe submitted observations; they do not establish root cause."
    }

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

    def do_GET(self):
        if self.path == "/health":
            return self.reply(200, {"ok":True,"service":"ps4-reporting"})
        if self.path == "/api/stats":
            return self.reply(200, build_stats())
        return self.reply(404, {"ok":False,"error":"not-found"})

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
