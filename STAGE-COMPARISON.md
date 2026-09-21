# Stage-Level Comparison

Stage-level analysis answers a different question from final success statistics: **how far did each submitted attempt get?**

The reference server derives stage reach from each report's explicit event history plus its last observed stage. It then groups observations by firmware and build.

## Output

`GET /api/stats` now includes:

- `stageReach` — reach count and percentage for every observed stage in each firmware/build group.
- `stageComparisons` — percentage-point changes between builds on the same firmware.
- `signal: true` when both samples meet the minimum size and stage reach drops by the configured threshold.

Stages are host-defined. The reporting system does not require a particular exploit chain or assume every host uses the same milestones.

## Interpretation

If build A reaches a stage in 82% of comparable reports and build B reaches it in 55%, the result is a **27 percentage-point observed drop**. That is useful for triage, but it does not prove the stage itself caused failures.

For meaningful comparisons, keep firmware, host configuration, test conditions, and stage definitions consistent.

## Sample size

The default comparison threshold follows regression detection: at least 10 reports for each build and a 10 percentage-point drop before a stage signal is emitted.
