#!/usr/bin/env python3
import json, os, tempfile, importlib.util

path=os.path.join(os.path.dirname(__file__),"..","server","server.py")
spec=importlib.util.spec_from_file_location("report_server",path)
mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)

with tempfile.TemporaryDirectory() as d:
    mod.STORAGE=d
    samples=[
      {"firmware":{"version":"13.02"},"host":{"buildId":"a"},"test":{"status":"SUCCESS","lastStage":"JAILBREAK-COMPLETE"},"stability":{}},
      {"firmware":{"version":"13.02"},"host":{"buildId":"a"},"test":{"status":"FAILURE","lastStage":"KERNEL-START"},"stability":{"consoleShutdown":True}},
      {"firmware":{"version":"13.52"},"host":{"buildId":"b"},"test":{"status":"TIMEOUT","lastStage":"USERLAND-READY"},"stability":{"timeout":True}}
    ]
    for i,r in enumerate(samples):
        with open(os.path.join(d,str(i)+".json"),"w") as f: json.dump({"report":r},f)
    s=mod.build_stats()
    assert s["sampleSize"]==3
    assert s["statusCounts"]["SUCCESS"]==1
    assert s["lastStageCounts"]["KERNEL-START"]==1
    assert s["stabilityObservations"]["consoleShutdown"]==1
    print("PASS",json.dumps(s,indent=2))
