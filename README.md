# What is this?

This repository aggregates spam numbers from the FTC-DNC Registry over the past 90 days, for use in the [SpamBlocker](https://github.com/aj3423/SpamBlocker) app.

# How this works?
- This repo schedules a github workflow, triggered daily, what it does:
  - Download daily numbers from url:
    https://www.ftc.gov/sites/default/files/DNC_Complaint_Numbers_YYYY-MM-DD.csv
  - Add them to **90days.db**
  - Remove numbers older than 90 days from the .db
  - Generate **90days.csv** from the .db
- The **90days.csv** can be downloaded in SpamBlocker

# Why not use their API?

They do provide an [API](https://www.ftc.gov/developer/api/v0/endpoints/do-not-call-dnc-reported-calls-data-api) for downloading numbers, but
1. It requires email registration.
2. It only shows up to 50 numbers per request:
  > items_per_page:  the endpoint displays a maximum of 50 records per request – this is also the maximum value allowed.

  Fetching the full daily dataset would require 5000+ HTTP requests...
