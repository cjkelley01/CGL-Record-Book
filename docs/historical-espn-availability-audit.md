# Batch 1: Historical ESPN data availability audit

## Existing evidence

- The historical season replay already succeeds for 2024 and 2025, but its future-week
  inputs are explicitly **prior completed-week projection persistence proxies**.
- The repository contains a historical weekly roster projection audit and an ESPN
  historical discovery client. These establish retrospective availability of player
  statistics, **not** when projections were originally published.
- The checked-in `data/raw/` directory contains only `.gitkeep`. Authenticated
  raw API captures are not committed to the repository.
- The current forecast pipeline uses `mRoster` with a target `scoringPeriodId`
  for rostered-player week-specific projections; it does not demonstrate that
  those values can be recovered *as they existed at an earlier date*.

## Questions the new probe answers

1. Can authenticated ESPN requests retrieve historical `mRoster` for both a
   cutoff week and a later target week?
2. How many player entries in each response include exactly one projected
   score for that later target week?
3. Do returned team roster memberships differ between the two week queries?
4. Are there missing or duplicate target-week projection records?

The sanitized artifact records only aggregate counts, HTTP status, and errors.
It does not include cookies, player IDs, names, or raw roster payloads.

## What this probe cannot establish

A 2026 request for a 2024 projection cannot prove that the same number was
available in Week 7 of 2024. Similarly, an old scoringPeriodId is not proof
of an archived roster snapshot. ESPN may return revised or finalized values.

Therefore, **do not feed these retrospective future-week numbers directly into
a leakage-free historical replay** without independently dated captures.

## Running the probe

After merging the PR, open **Actions → Historical ESPN Availability Audit
(manual) → Run workflow**. Default pairs are 2024 and 2025, cutoff weeks 7
and 10, target weeks 10 and 13. The workflow uses existing ESPN GitHub
secrets, and uploads `historical-espn-availability-audit`.

If authentication fails, the report still uploads. Do not paste ESPN cookies
into issues or logs.

## Decision gate for Batch 2

- **Historical rosters + reliable dated projections:** reconstruct authentic
  point-in-time lineup forecasts.
- **Historical rosters but no dated future projections:** replay roster
  structure using strictly cutoff-available player performance estimates;
  label this a proxy model, not ESPN's historical forecasts.
- **Neither reliably available:** prioritize archived 2026 weekly forecast
  snapshots and prospective validation rather than pretend retrospective
  projections were known.

No production forecast settings are changed in Batch 1.
