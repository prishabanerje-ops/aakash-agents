# Scheduling, Automation & CI/CD

## The #1 Cron Failure: Missing Environment Variables

When SF runs via cron, it doesn't inherit your login shell environment.
The two most critical missing variables:

```bash
DISPLAY=:99    # Virtual display — SF will hang without this
JAVA_HOME=...  # If SF can't find Java, silent failure
```

**Always set these explicitly in cron jobs.**

---

## Cron Setup

### Add to crontab
```bash
crontab -e
```

### Daily crawl at 3 AM
```cron
# Set required environment variables
DISPLAY=:99
JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

# Cars24 New Cars — daily audit
0 3 * * * /usr/local/bin/run-cars24-audit.sh >> /var/log/sf-audit.log 2>&1
```

### Wrapper script (recommended over inline cron commands)

```bash
#!/bin/bash
# /usr/local/bin/run-cars24-audit.sh

set -euo pipefail

# Environment
export DISPLAY=:99
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
export PATH="$JAVA_HOME/bin:$PATH"

# Config
DATE=$(date +%Y%m%d_%H%M)
PROPERTY="cars24-new-cars"
OUTPUT_BASE="/data/seo-audits"
OUTPUT_DIR="$OUTPUT_BASE/$PROPERTY-$DATE"
LOG_FILE="$OUTPUT_BASE/logs/$PROPERTY-$DATE.log"
LOCK_FILE="/tmp/sf-crawl.lock"
CONFIG="/etc/screaming-frog/cars24-production.seospiderconfig"

# Concurrent run protection
if [ -f "$LOCK_FILE" ]; then
  echo "$(date): Crawl already running (lock file exists). Exiting." >> "$LOG_FILE"
  exit 0
fi
touch "$LOCK_FILE"
trap "rm -f $LOCK_FILE" EXIT

# Ensure Xvfb is running
if ! pgrep -x Xvfb > /dev/null; then
  echo "$(date): Starting Xvfb" >> "$LOG_FILE"
  Xvfb :99 -screen 0 1024x768x24 -ac &
  sleep 2
fi

# Ensure output directory exists
mkdir -p "$OUTPUT_DIR"
mkdir -p "$(dirname $LOG_FILE)"

echo "$(date): Starting Cars24 audit — $OUTPUT_DIR" >> "$LOG_FILE"

# Run SF
timeout 7200 ScreamingFrogSEOSpider \
  --headless \
  --config "$CONFIG" \
  --crawl https://www.cars24.com/new-cars/ \
  --max-urls 1000 \
  --output-folder "$OUTPUT_DIR" \
  --overwrite \
  --save-crawl \
  --export-tabs "Internal:All,Response Codes:All,Page Titles:All,Meta Description:All,H1:All,H1:Duplicate,Canonical URL:All,Directives:All,Images:Missing Alt Text,Structured Data:All" \
  >> "$LOG_FILE" 2>&1

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
  echo "$(date): Crawl COMPLETED successfully" >> "$LOG_FILE"
  # Post-crawl hook
  /usr/local/bin/post-crawl-hook.sh "$OUTPUT_DIR" >> "$LOG_FILE" 2>&1
else
  echo "$(date): Crawl FAILED with exit code $EXIT_CODE" >> "$LOG_FILE"
  # Alert on failure
  curl -s -X POST "https://hooks.slack.com/services/YOUR/WEBHOOK/URL" \
    -H 'Content-type: application/json' \
    --data "{\"text\":\"✗ Cars24 SF crawl failed (exit $EXIT_CODE) — check $LOG_FILE\"}" \
    >> "$LOG_FILE" 2>&1
fi

echo "$(date): Done" >> "$LOG_FILE"
```

### Post-crawl hook

```bash
#!/bin/bash
# /usr/local/bin/post-crawl-hook.sh

OUTPUT_DIR="$1"

# 1. Validate outputs
CSV_COUNT=$(ls "$OUTPUT_DIR"/*.csv 2>/dev/null | wc -l)
echo "CSV files produced: $CSV_COUNT"

# 2. Convert to XLSX (optional)
python3 /usr/local/bin/csv-to-xlsx.py "$OUTPUT_DIR"

# 3. Upload to Google Drive (optional)
# rclone copy "$OUTPUT_DIR" gdrive:cars24-seo-audits/ --quiet

# 4. Send Slack summary
URLS=$(wc -l < "$OUTPUT_DIR/internal_html.csv" 2>/dev/null || echo "?")
curl -s -X POST "https://hooks.slack.com/services/YOUR/WEBHOOK/URL" \
  -H 'Content-type: application/json' \
  --data "{\"text\":\"✓ Cars24 SF audit done — $URLS URLs crawled — $OUTPUT_DIR\"}"
```

---

## Test S1 — Cron Job Fires

```bash
# Test the wrapper script directly first
sudo -u www-data /usr/local/bin/run-cars24-audit.sh
echo "Exit: $?"

# Then test as cron would run it (no environment)
env -i HOME=/root /bin/bash /usr/local/bin/run-cars24-audit.sh
echo "Exit: $?"
```

## Test S3 — Environment Variables in Cron

```bash
# Diagnostic: what does cron's environment look like?
# Add this temporary cron job:
# * * * * * env > /tmp/cron-env.txt

cat /tmp/cron-env.txt | grep -E "DISPLAY|JAVA|PATH"
# Should show your exports; if not, add them to crontab explicitly
```

## Test S6 — Lock File Works

```bash
# Simulate concurrent run
touch /tmp/sf-crawl.lock
/usr/local/bin/run-cars24-audit.sh
echo "Exit: $?"  # Should exit 0 with "already running" message
rm /tmp/sf-crawl.lock
```

---

## GitHub Actions Integration

For CI/CD usage (running audits on schedule or PR trigger):

```yaml
# .github/workflows/seo-audit.yml
name: Cars24 SEO Audit

on:
  schedule:
    - cron: '0 3 * * 1'  # Weekly on Monday 3am UTC
  workflow_dispatch:      # Manual trigger

jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install Screaming Frog
        run: |
          wget -q https://download.screamingfrog.co.uk/products/seo-spider/screamingfrogseospider_21.x_amd64.deb
          sudo dpkg -i screamingfrogseospider_21.x_amd64.deb

      - name: Install Xvfb
        run: sudo apt-get install -y xvfb

      - name: Start virtual display
        run: |
          Xvfb :99 -screen 0 1024x768x24 &
          echo "DISPLAY=:99" >> $GITHUB_ENV

      - name: Activate license
        run: ScreamingFrogSEOSpider --activate-license ${{ secrets.SF_LICENSE_KEY }}

      - name: Run audit
        run: |
          ScreamingFrogSEOSpider \
            --headless \
            --crawl https://www.cars24.com/new-cars/ \
            --max-urls 500 \
            --output-folder ${{ github.workspace }}/audit-output \
            --overwrite \
            --export-tabs "Internal:All,Response Codes:All,H1:All,Page Titles:All"

      - name: Upload results
        uses: actions/upload-artifact@v4
        with:
          name: seo-audit-${{ github.run_id }}
          path: audit-output/
          retention-days: 30

      - name: Check for critical issues
        run: |
          # Fail the workflow if 4xx errors found
          ERRORS=$(grep -c "^[^,]*,[^,]*,4[0-9][0-9]" audit-output/response_codes_all.csv 2>/dev/null || echo 0)
          echo "4xx errors found: $ERRORS"
          if [ "$ERRORS" -gt 10 ]; then
            echo "✗ Too many 4xx errors ($ERRORS). Investigate."
            exit 1
          fi
```

---

## Alerting on Crawl Issues

```bash
#!/bin/bash
# /usr/local/bin/sf-alert-check.sh — run after every crawl

OUTPUT_DIR="$1"

# Check 1: 5xx errors
ERRORS_5XX=$(tail -n +2 "$OUTPUT_DIR/response_codes_all.csv" 2>/dev/null | \
  awk -F',' '$3 ~ /^5/' | wc -l)
[ "$ERRORS_5XX" -gt 0 ] && echo "⚠  5xx errors: $ERRORS_5XX"

# Check 2: Missing H1s
MISSING_H1=$(wc -l < "$OUTPUT_DIR/h1_missing.csv" 2>/dev/null || echo 0)
[ "$MISSING_H1" -gt 5 ] && echo "⚠  Missing H1s: $MISSING_H1"

# Check 3: Missing title tags
MISSING_TITLE=$(grep -c "^[^,]*,," "$OUTPUT_DIR/page_titles_all.csv" 2>/dev/null || echo 0)
[ "$MISSING_TITLE" -gt 0 ] && echo "⚠  Missing title tags: $MISSING_TITLE"

# Check 4: Duplicate titles
DUP_TITLES=$(wc -l < "$OUTPUT_DIR/page_titles_duplicate.csv" 2>/dev/null || echo 0)
[ "$DUP_TITLES" -gt 3 ] && echo "⚠  Duplicate titles: $DUP_TITLES"
```
