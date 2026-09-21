# Stability Analysis

The reference server can aggregate submitted reports so developers can identify recurring failure patterns without manually reading every JSON file.

## Endpoints

### `GET /health`

Returns a minimal service-health response.

### `GET /api/stats`

Returns aggregate observations from the server's report storage.

The response includes:

- total sample size
- outcome/status counts
- report counts by firmware
- last-observed-stage counts
- report counts by build
- stability observations
- firmware/build success comparisons

Example:

```json
{
  "sampleSize": 142,
  "statusCounts": {
    "SUCCESS": 91,
    "FAILURE": 31,
    "TIMEOUT": 12,
    "INTERRUPTED": 8
  },
  "lastStageCounts": {
    "JAILBREAK-COMPLETE": 91,
    "KERNEL-START": 27,
    "PRIMITIVE-READY": 14
  }
}
```

## Reading the data correctly

A large count at a particular last-observed stage is a signal to investigate. It is **not proof that the stage caused the failure**.

Always consider sample size, firmware, build, implementation, configuration, and whether the observations came from comparable hardware/test conditions.

## Regression analysis

Compare the same firmware across host build IDs. A drop in completion rate or an increase in a particular interruption type after a build change can identify a regression candidate.

Do not treat small samples as definitive. Keep raw reports available to developers for reproduction and deeper analysis.

## Privacy

The statistics endpoint intentionally returns aggregates rather than raw community reports. Do not expose raw submissions publicly unless testers were explicitly informed and the data has been reviewed for privacy.
