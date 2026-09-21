# Integration Guide

## 1. Add the client

Copy `reporting-client.js` into your WebKit host and load it before your jailbreak/test scripts:

```html
<script src="./reporting-client.js"></script>
```

## 2. Create a report session

Create one session for every execution attempt:

```javascript
var report = new PS4ReportingClient({
  endpoint: "https://YOUR-DOMAIN.example/api/community-report",
  firmware: { version: detectedFirmware, source: "host-detection" },
  host: { name: "Your Host", version: "1.0.0", buildId: "build-001" },
  attempt: 1
});
```

Do not include a real name, PSN account, serial number, MAC address, or precise location.

## 3. Instrument existing milestones

Add reporting calls beside existing code. Do not restructure a working exploit solely for reporting.

```javascript
report.stage("WEBKIT-READY");
report.stage("USERLAND-START");

// after confirmed userland milestone
report.stage("USERLAND-READY");
report.setState("userland", "VERIFIED");

// after confirmed primitive milestone
report.stage("PRIMITIVE-READY");

// before/after implementation-defined later stages
report.stage("KERNEL-START");
report.stage("PAYLOAD-START");
```

Only mark a state VERIFIED when the host actually verified it.

## 4. Record outcomes

```javascript
report.success();
report.failure("YOUR-FAILED-STAGE");
report.timeout("YOUR-TIMED-OUT-STAGE");
report.observe("browserHang");
report.observe("kernelFaultObserved");
```

An observation is not automatically a cause. A checkpoint immediately before a shutdown should be described as the last observed stage, not as proof that stage caused the shutdown.

## 5. Submit

```javascript
report.submit()
  .then(function (result) { console.log(result.submissionId); })
  .catch(function (error) { console.log(error.message); });
```

Manual, visible submission is recommended. Tell testers what is being sent.

## 6. Crash/interruption recovery

The client checkpoints the active report to localStorage. On the next page load:

```javascript
var previous = PS4ReportingClient.recoverInterrupted();
if (previous) {
  // Show the tester a preview and an explicit submit/discard choice.
}
```

## 7. Run your own server

The reference API is in `server/server.py`.

```bash
REPORT_ALLOWED_ORIGIN="https://your-host.example" \
REPORT_STORAGE="./reports" \
python3 server/server.py
```

For an Internet-facing deployment, place it behind HTTPS, restrict CORS to your host, enforce request-size/rate limits, validate reports, protect stored data, and define a retention policy.

## Compatibility

The reporting layer is firmware-independent. Your host decides what firmware, exploit implementation, payload, and stages it supports.
