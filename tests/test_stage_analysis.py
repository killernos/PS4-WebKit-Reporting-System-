#!/usr/bin/env python3
import os, importlib.util
path=os.path.join(os.path.dirname(__file__),"..","server","server.py")
spec=importlib.util.spec_from_file_location("report_server",path)
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

def row(build, stages):
    return {"firmware":{"version":"13.02"},"host":{"buildId":build},
            "events":[{"stage":x} for x in stages],
            "test":{"lastStage":stages[-1] if stages else "UNKNOWN"}}

reports=[]
reports += [row("a",["WEBKIT-READY","USERLAND-READY","PRIMITIVE-READY"]) for _ in range(10)]
reports += [row("b",["WEBKIT-READY","USERLAND-READY"]) for _ in range(5)]
reports += [row("b",["WEBKIT-READY"]) for _ in range(5)]
sr=m.stage_analysis(reports)
assert len(sr)==2
cmp=m.stage_comparisons(sr,min_samples=10,warn_delta=10)
primitive=[x for x in cmp[0]["stages"] if x["stage"]=="PRIMITIVE-READY"][0]
assert primitive["deltaPoints"] == -100.0
assert primitive["signal"] is True
print("PASS",cmp[0])
