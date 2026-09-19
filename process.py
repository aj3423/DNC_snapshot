import csv
import sqlite3
import time
import sys
from datetime import datetime
import time
import io
import requests
import re


class DB:
    def __init__(self, db_path, expiry_days):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self.expiry_days = expiry_days
        self.init()

    # create table if not exists
    def init(self):
        self.execute("""
            CREATE TABLE IF NOT EXISTS numbers (
                number TEXT,
                timestamp INTEGER
            )
        """)

        self.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON numbers (timestamp)")

    def execute(self, query, params=()):
        self.cursor.execute(query, params)
        self.conn.commit()
        return self.cursor

    # Add numbers from CSV content
    def add_csv(self, csv_str) -> int:
        now = int(time.time())
        reader = csv.reader(io.StringIO(csv_str))
        next(reader, None)  # Skip header row
        data = []
        for row in reader:
            if row and len(row) > 0:
                num = row[0].strip()

                if num:
                    data.append((num, now))

        # Bulk insert with `executemany`
        self.cursor.executemany(
            "INSERT INTO numbers (number, timestamp) VALUES (?, ?)", data
        )
        self.conn.commit()

        return len(data)

    # Remove records older than `self.expiry_days`
    def prune(self) -> int:
        now = int(time.time())
        cutoff = now - (self.expiry_days * 24 * 3600)
        deleted = self.execute(
            "DELETE FROM numbers WHERE timestamp < ?", (cutoff,)
        ).rowcount
        return deleted

    # Export all numbers to CSV
    def generate_csv(self):
        output_csv = self.db_path.replace(".db", ".csv")
        self.cursor.execute("SELECT number FROM numbers")
        rows = self.cursor.fetchall()
        with open(output_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["pattern"])  # Write header
            for row in rows:
                writer.writerow([row[0]])
        return len(rows)

    def close(self):
        self.conn.close()


def http_request(
    url,
    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    retries=3,
    retry_delay=1,
):
    headers = {"User-Agent": user_agent}
    for _ in range(retries + 1):
        try:
            r = requests.get(url, headers=headers, timeout=30)
            r.raise_for_status()
            return r
        except:
            time.sleep(retry_delay)
    raise Exception(f"All attempts failed for URL: {url}")


def extract_paths_from_html(html: str) -> list[str]:
    return re.findall(r'href="([^"]+\.csv)"', html)


def extract_date_from_path(path: str) -> str:
    return re.search(r"(\d{4}-\d{2}-\d{2})", path).group(1)


def main():
    # 1. Get the HTML of the FTC Do Not Call Data page
    r = http_request(
        "https://www.ftc.gov/policy-notices/open-government/data-sets/do-not-call-data"
    )
    html = r.text

    # 2. Extract a list of:
    # [
    #     '/sites/default/files/DNC_Complaint_Numbers_2026-01-12.csv',
    #     '/sites/default/files/DNC_Complaint_Numbers_2026-01-13.csv',
    #     ...
    # ]
    paths = extract_paths_from_html(html)

    # 3. filter paths to only include those with dates after checkpoint
    # Load the last processed csv date
    lcd = "last_csv_date.txt"
    with open(lcd) as f:
        last_csv_date = f.read().strip()
    paths = list(filter(lambda p: extract_date_from_path(p) > last_csv_date, paths))

    # Sort in ascending order
    paths.sort()

    # 4. Update databases
    db_90_day = DB("90days.db", expiry_days=90)
    db_daily = DB("daily.db", expiry_days=1)

    if paths:  # if there are new CSVs to process
        for p in paths:
            date = extract_date_from_path(p)  # e.g. '2026-01-12'
            print(date)

            # 1. download the csv
            csv_str = http_request(f"https://www.ftc.gov{p}").text

            # 2. 90 days db
            n = db_90_day.add_csv(csv_str)
            print(f"Inserted {n} numbers to 90days.db")

            # 3. daily db
            n = db_daily.add_csv(csv_str)
            print(f"Inserted {n} numbers to daily.db")

            # 4. update last_csv_date
            last_csv_date = date

        # update `last_csv_date.txt`
        with open(lcd, "w") as f:
            f.write(last_csv_date)

    else:
        print("No new files published, likely weekend/holiday/government shutdown.")
        print(
            "Check it on their website: https://www.ftc.gov/policy-notices/open-government/data-sets/do-not-call-data"
        )

    # 5. prune and generate csv for both dbs
    db_90_day.prune()
    db_90_day.generate_csv()
    db_90_day.close()

    db_daily.prune()
    db_daily.generate_csv()
    db_daily.close()


main()
