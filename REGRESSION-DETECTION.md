# Automated Regression Detection

The reference server compares successive observed build IDs **within the same firmware**.

## Signals

By default, a comparison becomes eligible after each build has at least 10 submitted reports. It emits an investigation signal when a rate changes by at least 10 percentage points in an unfavorable direction:

- `SUCCESS_RATE_DROP`
- `TIMEOUT_RATE_INCREASE`
- `SHUTDOWN_RATE_INCREASE`
- `BROWSER_CRASH_RATE_INCREASE`

Every comparison includes both sample sizes, baseline/current rates, percentage-point deltas, and an interpretation.

## Important limitations

These are **triage signals**, not proof that a build caused a regression. Community samples can differ in hardware conditions, host configuration, exploit/payload selection, tester behavior, network conditions, and other variables.

Build ordering uses the first observed report timestamp where available. Projects with formal release metadata may want to replace this with their own release ordering.

## Recommended workflow

When a signal appears, inspect the underlying reports, reproduce on controlled hardware, compare the same firmware/configuration, and then decide whether the build change is responsible.

Thresholds are intentionally conservative defaults and can be changed in `regression_analysis()`.
