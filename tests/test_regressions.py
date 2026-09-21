#!/usr/bin/env python3
import os, importlib.util
path=os.path.join(os.path.dirname(__file__),"..","server","server.py")
spec=importlib.util.spec_from_file_location("report_server",path)
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

def row(build,status,crash=False,shutdown=False,timeout=False):
    return {"timestamp":"2026-09-21T00:00:00Z" if build=="a" else "2026-09-22T00:00:00Z",
      "firmware":{"version":"13.02"},"host":{"buildId":build},
      "test":{"status":status},"stability":{"browserCrash":crash,"consoleShutdown":shutdown,"timeout":timeout}}

reports=[]
reports += [row("a","SUCCESS") for _ in range(10)]
reports += [row("b","SUCCESS") for _ in range(5)]
reports += [row("b","FAILURE",crash=True) for _ in range(5)]
r=m.regression_analysis(reports,min_samples=10,warn_delta=10.0)
assert len(r)==1
assert r[0]["sufficientSample"] is True
assert "SUCCESS_RATE_DROP" in r[0]["signals"]
assert "BROWSER_CRASH_RATE_INCREASE" in r[0]["signals"]
print("PASS",r[0])
