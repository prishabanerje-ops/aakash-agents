# API Integrations — GSC, GA4, PageSpeed, Majestic

## Token Storage Location

SF stores OAuth tokens here:
```bash
ls ~/.ScreamingFrogSEOSpider/
# Look for: google_oauth_token.json, ga4_token.json, etc.
```

---

## Google Search Console Integration

### Prerequisites
1. SF must be authenticated via GUI first (OAuth flow)
2. Token saved to `~/.ScreamingFrogSEOSpider/`
3. GSC property verified (exact match or domain property)

### Test Command
```bash
DISPLAY=:99 ScreamingFrogSEOSpider \
  --headless \
  --config /path/to/config.seospiderconfig \
  --crawl https://www.cars24.com/new-cars/ \
  --max-urls 100 \
  --output-folder /tmp/sf-gsc-test \
  --overwrite \
  --export-tabs "Internal:All" \
  2>&1

# Check for GSC columns in output
head -1 /tmp/sf-gsc-test/internal_html.csv | tr ',' '\n' | grep -iE "impression|click|position"
```

### Expected GSC columns in export
```
Impressions
Clicks
CTR
Position
```

### GSC Auth Failure Patterns
```
# Pattern 1: Token expired
Error: 401 Unauthorized
Fix: Re-authenticate via SF GUI > Configuration > API Access > Google Search Console

# Pattern 2: Wrong property
No data returned, 0 impressions everywhere
Fix: Check property URL matches exactly (trailing slash matters)
# www.cars24.com/new-cars/ ≠ https://www.cars24.com/new-cars/

# Pattern 3: Service account not added to GSC
Error: 403 Forbidden / insufficient permissions
Fix: Add service account email as "Full User" in GSC Settings > Users and permissions

# Pattern 4: Token file missing
Fix: Run SF GUI once on the server to authenticate, or copy token from dev machine
scp ~/.ScreamingFrogSEOSpider/google_oauth_token.json user@server:~/.ScreamingFrogSEOSpider/
```

### Service Account Method (more reliable for headless)

1. Create service account in Google Cloud Console
2. Download JSON key file
3. Add service account email to GSC as "Full User"
4. In SF: Configuration > API Access > Google Search Console > Use Service Account
5. Point to the JSON key file

```bash
# Verify service account file exists
ls -la /path/to/service-account-key.json
cat /path/to/service-account-key.json | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['client_email'])"
```

---

## Google Analytics 4 Integration

### Prerequisites
1. GA4 property ID (format: 123456789 — NOT UA-XXXXXX)
2. Same OAuth or service account as GSC
3. SF 20+ required for GA4 (older versions only support UA)

### Test Command
```bash
# GA4 is configured via saved config, not direct CLI flags
# Verify via column check after crawl
head -1 /tmp/sf-output/internal_html.csv | tr ',' '\n' | grep -iE "session|user|engagement"
```

### Expected GA4 columns
```
Sessions
Engaged Sessions
Engagement Rate
```

---

## PageSpeed Insights Integration

### Prerequisites
- PageSpeed API key (free from Google Cloud Console)
- Set in SF: Configuration > API Access > PageSpeed Insights

### Test Command
```bash
# PSI runs on crawled URLs — check pagespeed.csv in output
DISPLAY=:99 ScreamingFrogSEOSpider \
  --headless \
  --config /path/to/config-with-psi.seospiderconfig \
  --crawl https://www.cars24.com/new-cars/ \
  --max-urls 5 \
  --output-folder /tmp/sf-psi-test \
  --overwrite

ls /tmp/sf-psi-test/
# Expected: pagespeed.csv or Page_Speed.csv
head -2 /tmp/sf-psi-test/pagespeed*.csv 2>/dev/null
```

### Expected PSI columns
```
URL
Performance Score
First Contentful Paint
Largest Contentful Paint
Total Blocking Time
Cumulative Layout Shift
Speed Index
```

### PSI Failure Patterns
```
# Quota exceeded (free tier: 25k requests/day, 400/100sec)
Error: 429 Too Many Requests
Fix: Add API key, or reduce crawl size

# API key not set
Returns 0 or empty PSI data
Fix: Configuration > API Access > PageSpeed Insights > enter API key
```

---

## Majestic Integration (if licensed)

### Test Command
```bash
# Check for Majestic columns
head -1 /tmp/sf-output/internal_html.csv | tr ',' '\n' | grep -iE "trust|citation|flow|backlink"
```

### Expected columns
```
Majestic Trust Flow
Majestic Citation Flow
Majestic Referring Domains
Majestic External Backlinks
```

---

## Integration Health Check Script

```bash
#!/bin/bash
# integrations-check.sh — Run after a crawl to verify all integrations fired

OUTPUT_DIR="${1:-/tmp/sf-latest}"
CSV="$OUTPUT_DIR/internal_html.csv"

if [ ! -f "$CSV" ]; then
  echo "✗ No internal_html.csv found in $OUTPUT_DIR"
  exit 1
fi

HEADER=$(head -1 "$CSV")

check_columns() {
  local name="$1"
  shift
  local found=0
  for col in "$@"; do
    echo "$HEADER" | grep -qi "$col" && found=1
  done
  if [ $found -eq 1 ]; then
    echo "✓ $name integration: columns present"
  else
    echo "✗ $name integration: columns MISSING"
  fi
}

check_columns "GSC"        "Impressions" "Clicks" "Position"
check_columns "GA4"        "Sessions" "Engaged Sessions"
check_columns "PageSpeed"  "Performance Score" "LCP" "CLS"
check_columns "Majestic"   "Trust Flow" "Citation Flow"
```

Save as `/usr/local/bin/sf-integrations-check.sh` and run after each audit crawl.
