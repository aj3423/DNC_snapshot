## What is this?

This repository aggregates spam numbers from the [FTC-DNC Registry](https://www.ftc.gov/policy-notices/open-government/data-sets/do-not-call-data) over the past 90 days, for use in the [SpamBlocker](https://github.com/aj3423/SpamBlocker) app.

## How this works?
This repo schedules a github workflow, runs daily at 17:00 EST (UTC-5), what it does:
  - Check if there are new CSV files published on:
    https://www.ftc.gov/policy-notices/open-government/data-sets/do-not-call-data
  - If new files are found, download them and import into the database `90days.db` and `daily.db`:
  - Prune numbers older than 90 days from `90days.db` and numbers older than 1 day from `daily.db`
  - Generate two CSV from them:
    - `90days.csv`, for initial setup, it contains all numbers from the past 90 days
    - `daily.csv`, for incremental updates, it only contains new numbers 

## Problems this repo solves
1. The FTC is often slow to update the list, e.g. publishing Monday’s data on Wednesday.
2. The filename can be malformed, e.g. [2026-01-09_0.csv](https://www.ftc.gov/sites/default/files/DNC_Complaint_Numbers_2026-01-09_0.csv) (with an extra `_0`)
