# Non-Legacy PS4 Firmware Compatibility

This project is a diagnostics and stability-reporting layer for non-legacy PS4 WebKit hosts.

## Important distinction

Reporting compatibility does **not** mean jailbreak compatibility. A firmware can participate in diagnostics even when a host has no completed exploit chain for it.

## Firmware policy

The reporting protocol intentionally does not contain a hard-coded firmware allowlist. Implementing hosts define what they consider non-legacy and can supply a compatibility state:

- `SUPPORTED` — the host considers its implementation supported on this firmware.
- `EXPERIMENTAL` — implementation exists but is still being stabilized.
- `RESEARCH` — diagnostics/research only; no completed jailbreak is implied.
- `UNKNOWN` — compatibility has not been classified.

Unknown/new firmware strings should remain reportable instead of causing schema rejection.

## Capability model

Do not infer capabilities from firmware alone. Report them explicitly:

```javascript
report.setCompatibility("RESEARCH");
report.setCapability("webKit", "AVAILABLE");
report.setCapability("userland", "UNKNOWN");
report.setCapability("readPrimitive", "UNKNOWN");
report.setCapability("writePrimitive", "UNKNOWN");
report.setCapability("kernel", "NOT_TESTED");
report.setCapability("payload", "NOT_TESTED");
```

Suggested capability states are `AVAILABLE`, `VERIFIED`, `UNAVAILABLE`, `FAILED`, `NOT_TESTED`, and `UNKNOWN`.

## Host responsibility

Each integrating host is responsible for:
1. Detecting or supplying its firmware version.
2. Deciding whether that firmware is in its non-legacy scope.
3. Declaring compatibility/capabilities from actual observations.
4. Defining meaningful stage names for its implementation.
5. Never presenting reporting support as proof of exploit or jailbreak support.

This keeps the reporting format reusable as firmware research changes.
