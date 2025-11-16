import csv
import sqlite3
import time
import sys
from datetime import datetime
import urllib.request

try:
    # Get today's date in YYYY-MM-DD format
    DATE = datetime.now().strftime("%Y-%m-%d")

    # Construct URL
    URL = f"https://www.ftc.gov/sites/default/files/DNC_Complaint_Numbers_{DATE}.csv"

    # Download the CSV with retry
    downloaded = False
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                URL,
                headers={"User-Agent": "SpamBlocker"},
            )
            with urllib.request.urlopen(req) as response:
                with open("dnc_daily.csv", "wb") as f:
                    f.write(response.read())

            print("Downloaded successfully", file=sys.stderr)
            downloaded = True
            break
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}", file=sys.stderr)
            if attempt < 2:
                time.sleep(5)  # Wait 5 seconds before retry

    if not downloaded:
        print("Failed to download CSV after 3 attempts", file=sys.stderr)
        print(
            f"Maybe due to weekend or holiday, the file isn't published: {URL}",
            file=sys.stderr,
        )
        sys.exit(2)

    # Connect to SQLite database
    conn = sqlite3.connect("90days.db")
    c = conn.cursor()

    # Create table if not exists
    c.execute("""
        CREATE TABLE IF NOT EXISTS numbers (
            number TEXT,
            timestamp INTEGER
        )
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON numbers (timestamp)")

    # Read CSV and insert numbers with current timestamp
    now = int(time.time())
    with open("dnc_daily.csv", "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader, None)  # Skip header row
        inserted = 0
        for row in reader:
            if row and len(row) > 0:
                num = row[0].strip()
                if num:
                    c.execute(
                        "INSERT INTO numbers (number, timestamp) VALUES (?, ?)",
                        (num, now),
                    )
                    inserted += 1
        print(f"Inserted {inserted} numbers.", file=sys.stderr)

    conn.commit()

    # Remove records older than 90 days
    cutoff = now - (90 * 24 * 3600)
    deleted = c.execute("DELETE FROM numbers WHERE timestamp < ?", (cutoff,)).rowcount
    conn.commit()
    print(f"Deleted {deleted} expired records.", file=sys.stderr)

    # Generate 90days.csv with only the number column
    c.execute("SELECT number FROM numbers")
    rows = c.fetchall()
    with open("90days.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["pattern"])  # Write header
        for row in rows:
            writer.writerow([row[0]])
    print(f"Generated 90days.csv with {len(rows)} numbers.", file=sys.stderr)

    conn.close()
    print("Processing completed successfully.", file=sys.stderr)

except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)
