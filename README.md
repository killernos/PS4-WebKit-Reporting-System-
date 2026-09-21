PS4 Universal Jailbreak Diagnostics & Stability Reporting

Find where PS4 jailbreaks fail. Reproduce it. Measure it. Stabilize it.

A universal, open-source diagnostics and community reporting framework for PS4 WebKit hosts, jailbreak implementations, exploit chains, and payload loaders across all firmware versions.

## Non-Legacy Firmware Scope

This project targets **non-legacy PS4 firmware** as a reporting and stability-analysis framework. It deliberately does not hard-code a firmware allowlist: the integrating WebKit host defines its non-legacy range, while unknown and future firmware values remain reportable for research.

Reporting compatibility does **not** mean jailbreak compatibility. Each host should declare a firmware as `SUPPORTED`, `EXPERIMENTAL`, `RESEARCH`, or `UNKNOWN`, and report observed capabilities separately. See `COMPATIBILITY.md`.


The purpose of this project is simple:

Turn community jailbreak testing into structured, actionable stability data.

Instead of receiving reports like:

"It crashed."
"Worked after 4 tries."
"GoldHEN didn't load."
"My PS4 shut down."

developers can receive structured information showing what was running, how far execution progressed, what failed, and whether other testers are experiencing the same problem.

⸻

🎯 Project Goals

This framework is designed to help PS4 developers:

* Identify unstable jailbreak stages
* Find recurring failure patterns
* Compare stability between firmware versions
* Compare different WebKit/exploit implementations
* Measure success and failure rates
* Detect regressions between builds
* Track browser crashes
* Track browser hangs
* Track console shutdowns/reboots
* Track timeouts
* Track payload execution results
* Recover information from interrupted attempts
* Aggregate results from multiple testers
* Improve jailbreak reliability using real-hardware data

⸻

🌐 Universal Firmware Support

The reporting framework is firmware-independent.

It does not maintain a hard-coded firmware allowlist.

PS4 Firmware
     │
     ├── Legacy Firmware
     ├── Existing Jailbreak Firmware
     ├── Current Firmware
     ├── Experimental Firmware
     └── Future Firmware

The WebKit host determines which firmware it supports.

The reporting framework simply records the firmware reported by the implementation.

This allows one reporting system to be used across an entire WebKit host.

⸻

🔎 What Does It Solve?

A jailbreak normally contains several execution stages.

Example:

SESSION CREATED
       ↓
FIRMWARE DETECTED
       ↓
WEBKIT INITIALIZED
       ↓
USERLAND STARTED
       ↓
USERLAND READY
       ↓
PRIMITIVE INITIALIZATION
       ↓
EXPLOIT STAGE
       ↓
KERNEL STAGE
       ↓
PAYLOAD PREPARATION
       ↓
PAYLOAD EXECUTION
       ↓
JAILBREAK COMPLETE

When something fails, the reporting framework records the last confirmed stage.

Instead of:

Jailbreak failed.

a developer could receive:

Firmware:          X.XX
Host Build:        1.4.2
Exploit:           Example Exploit
Attempt:           3
Last Stage:        KERNEL-TRIGGER
Previous Stage:    USERLAND-READY
Browser Crash:     false
Browser Hang:      false
Console Shutdown:  true
Timeout:           false
Stage Runtime:     1842 ms

That gives developers a specific area to investigate.

⸻

📊 Stability Analysis

Once multiple testers submit reports, the system can identify patterns.

Example:

Attempts: 500
WEBKIT-READY          492
USERLAND-READY        471
PRIMITIVE-READY       443
KERNEL-TRIGGER        417
KERNEL-COMPLETE       326
PAYLOAD-COMPLETE      309

This makes it much easier to determine where reliability is being lost.

⸻

📈 Build Comparison

Every report should contain a host/build identifier.

This allows developers to compare releases.

Example:

                    Build 1.4.1     Build 1.4.2
Attempts                500             525
Completed               61%             74%
Browser Crash           18%             11%
Shutdown                12%              6%
Timeout                  9%              7%

This helps answer:

Did the new build actually improve stability?

⸻

🧪 Diagnostic Events

Developers can instrument important parts of their existing WebKit implementation.

Example:

report.stage("WEBKIT-READY");
report.stage("USERLAND-START");
report.stage("USERLAND-READY");
report.stage("PRIMITIVE-START");
report.stage("PRIMITIVE-READY");
report.stage("KERNEL-START");
report.stage("KERNEL-COMPLETE");
report.stage("PAYLOAD-START");
report.stage("PAYLOAD-COMPLETE");
report.success();

A failure can be recorded:

report.failure("PRIMITIVE-INITIALIZATION");

A timeout:

report.timeout("KERNEL-STAGE");

The reporting framework does not need to know how the exploit works.

It records the states provided by the implementation.

⸻

⏱️ Timing Diagnostics

Each stage can optionally include execution timing.

Example:

{
  "stage": "EXAMPLE-STAGE",
  "started": 184234,
  "completed": 185971,
  "durationMs": 1737,
  "result": "PASS"
}

Timing data can help identify situations where failures correlate with unusually fast or slow execution.

⸻

🧾 Universal Report Format

Example:

{
  "schema": "ps4-community-report-1",
  "reportId": "REPORT-XXXXXXXX",
  "sessionId": "SESSION-XXXXXXXX",
  "timestamp": "2026-09-21T12:00:00Z",
  "platform": "PS4",
  "firmware": {
    "version": "X.XX",
    "source": "user-agent"
  },
  "host": {
    "name": "Example WebKit Host",
    "version": "1.0",
    "buildId": "example-build-001"
  },
  "test": {
    "candidate": "example-test",
    "attempt": 1,
    "lastStage": "KERNEL-TRIGGER"
  },
  "state": {
    "userland": "VERIFIED",
    "readPrimitive": "VERIFIED",
    "writePrimitive": "VERIFIED",
    "kernel": "UNKNOWN"
  },
  "payload": {
    "name": "example-payload",
    "version": "1.0",
    "result": "NOT_ATTEMPTED"
  },
  "stability": {
    "browserCrash": false,
    "browserHang": false,
    "consoleShutdown": false,
    "consoleReboot": false,
    "kernelFaultObserved": false,
    "timeout": false
  },
  "diagnostics": []
}

Projects can extend this structure with their own diagnostic fields.

⸻

🔄 Attempt Tracking

Every execution should generate a unique session.

Example:

SESSION-A81K4Q
SESSION-P39MX2
SESSION-7DQL91

Reports can additionally record an attempt number:

Session: SESSION-P39MX2
Attempt: 4

This prevents multiple attempts from being accidentally treated as a single observation.

⸻

💥 Crash-Survival Reporting

One of the biggest challenges with browser-based diagnostics is that the browser may disappear before a failure report can be submitted.

The framework can optionally maintain a minimal local checkpoint.

Example:

SESSION=P39MX2
ATTEMPT=4
LAST_STAGE=KERNEL-TRIGGER
STATUS=RUNNING

After the browser is reopened, the reporting client can detect that the previous session never completed.

The tester can then be offered:

Previous test session was interrupted.
Firmware: X.XX
Attempt: 4
Last recorded stage: KERNEL-TRIGGER
[ Submit Interrupted Report ]
[ Discard ]

This provides useful crash-survival information without claiming that the recorded stage caused the interruption.

⸻

⚠️ Observation vs. Cause

This distinction is important.

If the final checkpoint before a console shutdown was:

KERNEL-TRIGGER

the reporting framework should state:

Last observed stage: KERNEL-TRIGGER
Console interruption observed.

It should not automatically claim:

KERNEL-TRIGGER caused the crash.

Correlation should be established from repeated testing and developer analysis.

⸻

🖥️ Recommended WebKit UI

A host implementing the framework should provide a simple reporting section.

Current Session

Firmware:      X.XX
Host Build:    1.4.2
Attempt:       3
Current Stage: KERNEL-TRIGGER

Diagnostics

Displays recorded test results and execution states.

Report Preview

Allows the tester to inspect what information will be submitted.

Submit Report

[ Submit Report ]

Submission Result

Report submitted successfully.
Submission ID:
XXXXXXXX

Automatic reporting should be optional and clearly disclosed.

⸻

🗄️ Server Architecture

The reporting framework does not require a centralized server.

Each project can operate its own endpoint.

PS4
 │
 ▼
WebKit Host
 │
 ▼
Diagnostic Collector
 │
 ▼
Report Builder
 │
 ▼
HTTP/HTTPS POST
 │
 ▼
Community Report API
 │
 ▼
Schema Validation
 │
 ▼
JSON / Database Storage
 │
 ▼
Analysis / Dashboard

The reporting endpoint should therefore be configurable.

Example:

const REPORT_ENDPOINT =
    "https://example.com/api/community-report";

⸻

📡 Example Submission

async function submitReport(report) {
    const response = await fetch(REPORT_ENDPOINT, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(report)
    });
    if (!response.ok) {
        throw new Error(
            "Report submission failed: " + response.status
        );
    }
    return response.json();
}

Projects should implement appropriate size limits, validation, abuse protection, and error handling on their servers.

⸻

📊 Developer Dashboard

Collected reports can be summarized through a dashboard.

Example:

PS4 JAILBREAK STABILITY
Total Attempts       2,481
Completed            1,937
Completion Rate      78.1%
FAILURE STAGES
Kernel Trigger         241
Primitive Setup        117
Payload Loader          83
Timeout                 46

Results can then be filtered by:

* Firmware
* WebKit host
* Build
* Exploit implementation
* Payload
* Execution stage
* Failure type
* Date
* Test configuration

⸻

🚨 Regression Detection

Aggregated reports can identify regressions between releases.

Example:

Build 1.4.1
Kernel-stage failures:
14 / 139
Build 1.4.2
Kernel-stage failures:
37 / 142

That does not automatically prove the new build caused the increase.

It identifies a change worth investigating.

⸻

🔐 Privacy

The base specification is designed around technical diagnostics rather than personal information.

Reports should not require:

* Real names
* Email addresses
* PSN usernames
* Passwords
* Account information
* Console serial numbers
* MAC addresses
* Precise location

Random session IDs should be used instead.

Server operators should clearly disclose any additional information their infrastructure records, including normal server logging.

⸻

🔧 Integration Philosophy

The framework should be easy to add to an existing project.

It should not require developers to rewrite their jailbreak.

The reporting layer sits beside the existing implementation:

Existing WebKit / Jailbreak
             │
             ├──────────────► Existing Execution
             │
             └──────────────► Diagnostic Events
                                      │
                                      ▼
                                Report Builder
                                      │
                                      ▼
                                Report Server

If the reporting system is removed, the underlying implementation should continue functioning normally.

⸻

🧩 Extensible Diagnostics

Projects can define additional diagnostic records.

Example:

{
  "id": "WEBKIT-001",
  "category": "runtime",
  "status": "PASS",
  "durationMs": 143,
  "details": {
    "message": "Runtime initialized"
  }
}

This allows specialized WebKit hosts to collect additional information without breaking compatibility with the base report format.

⸻

🤝 Community Adoption

This project is intended to provide a common reporting language across PS4 WebKit projects.

Developers are encouraged to:

* Integrate the reporting client
* Operate their own reporting endpoint
* Extend diagnostics for their implementation
* Share improvements
* Submit issues
* Contribute additional analysis tools
* Maintain compatibility with the common schema

The reporting framework should remain independent of any single WebKit host, jailbreak, payload, developer, or firmware.

⸻

⚠️ What This Project Is Not

This repository is a diagnostics and stability-reporting framework.

It does not itself provide or guarantee:

* A WebKit vulnerability
* A kernel vulnerability
* A kernel exploit
* A jailbreak
* Payload execution
* Compatibility with any particular firmware

Individual projects determine what they support.

⸻

🚀 Long-Term Goal

The long-term goal is to turn community testing into useful engineering data.

Instead of:

"It crashed again."

developers should be able to see:

Firmware X.XX
Build 1.4.2
142 attempts
37 attempts stopped after KERNEL-TRIGGER
31 produced the same interruption pattern
Median time before interruption:
1.82 seconds
Previous build:
14 / 139 attempts at the same stage

That gives developers something measurable and reproducible to investigate.

⸻

Core Principle

What was running?

Record the firmware, build, implementation and configuration.

How far did it get?

Record the last successfully completed stage.

What happened?

Record success, failure, timeout, crash, hang, reboot, shutdown, or interruption.

Is it repeatable?

Compare the result against other real-hardware reports.

⸻

Find it. Reproduce it. Measure it. Stabilize it.

Community testing becomes significantly more useful when everyone speaks the same diagnostic language.

Contributions, integrations, testing, bug reports, and improvements are welcome.

---

## Author & Credit

Created and maintained by **KillerNoS**.

If you implement or redistribute this framework, please retain the copyright and license notice included in the repository. Contributions and integrations from the PS4 development community are welcome.

## License

Released under the **MIT License**. See `LICENSE` for the full license text.


---

## Stability Analysis API

The reference server now provides `GET /api/stats` for aggregate community stability data and `GET /health` for service health. Aggregates include sample size, outcomes, firmware/build comparisons, last-observed-stage distribution, and stability observations. See `STABILITY-ANALYSIS.md` and `dashboard/index.html`.

Aggregated patterns identify areas worth investigating; they do not by themselves prove root cause.


## Automated Regression Detection

The statistics service now compares successive builds within each firmware and surfaces investigation signals for substantial drops in success rate or increases in timeout, shutdown, and browser-crash rates. Every comparison includes sample sizes and rate deltas. These are descriptive triage signals—not proof of causation. See `REGRESSION-DETECTION.md`.
