# Output Formats — CSV, XLSX, Google Sheets, Sitemaps

## Standard CSV Export

The most reliable output format. Always works in headless mode.

```bash
DISPLAY=:99 ScreamingFrogSEOSpider \
  --headless \
  --crawl https://www.cars24.com/new-cars/ \
  --max-urls 100 \
  --output-folder /tmp/sf-csv-test \
  --overwrite \
  --export-tabs "Internal:All,Response Codes:All,Page Titles:All,Meta Description:All,H1:All,H1:Duplicate,Canonical URL:All,Directives:All,Images:Missing Alt Text,Structured Data:All,Hreflang:All,Sitemaps:All"
```

### Expected output files
```
/tmp/sf-csv-test/
├── internal_all.csv              # All URLs crawled
├── internal_html.csv             # HTML pages only
├── response_codes_all.csv        # All response codes
├── page_titles_all.csv           # Title tags
├── meta_description_all.csv      # Meta descriptions
├── h1_all.csv                    # H1 tags
├── h1_duplicate.csv              # Duplicate H1s
├── canonical_url_all.csv         # Canonical tags
├── directives_all.csv            # Robots directives
├── images_missing_alt_text.csv   # Images without alt
├── structured_data_all.csv       # Schema markup
└── crawl_overview.csv            # Summary stats
```

### Validate CSV outputs
```bash
#!/bin/bash
OUTPUT_DIR="${1:-/tmp/sf-latest}"

EXPECTED_FILES=(
  "internal_all.csv"
  "internal_html.csv"
  "response_codes_all.csv"
  "page_titles_all.csv"
  "meta_description_all.csv"
  "h1_all.csv"
  "canonical_url_all.csv"
)

echo "=== CSV Output Validation ==="
for f in "${EXPECTED_FILES[@]}"; do
  if [ -f "$OUTPUT_DIR/$f" ]; then
    ROWS=$(wc -l < "$OUTPUT_DIR/$f")
    echo "✓ $f ($ROWS rows)"
  else
    echo "✗ MISSING: $f"
  fi
done

# Check for empty files (1 row = header only = empty)
echo ""
echo "=== Empty File Check ==="
for f in "$OUTPUT_DIR"/*.csv; do
  ROWS=$(wc -l < "$f")
  if [ "$ROWS" -le 1 ]; then
    echo "⚠  Empty (header only): $(basename $f)"
  fi
done
```

---

## XLSX Export

Requires SF 20+ and a valid license.

```bash
# XLSX export is via --save-report flag or post-crawl export
# Best approach: export CSV then convert with Python
python3 << 'EOF'
import pandas as pd
import os
from pathlib import Path

output_dir = Path('/tmp/sf-latest')
xlsx_path = output_dir / 'cars24-seo-audit.xlsx'

with pd.ExcelWriter(xlsx_path, engine='openpyxl') as writer:
    for csv_file in output_dir.glob('*.csv'):
        try:
            df = pd.read_csv(csv_file, low_memory=False)
            sheet_name = csv_file.stem[:31]  # Excel limit
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            print(f"✓ Added sheet: {sheet_name} ({len(df)} rows)")
        except Exception as e:
            print(f"✗ Failed {csv_file.name}: {e}")

print(f"\nXLSX saved: {xlsx_path}")
EOF
```

---

## Google Sheets Export

Requires pre-configured OAuth in SF and a target spreadsheet.

```bash
# Google Sheets export is configured in SF GUI first
# Then headless crawl writes to the sheet automatically if config is set

# Verify via the Sheets API after crawl
python3 << 'EOF'
# Verify sheet was updated (check last modified time)
try:
    from googleapiclient.discovery import build
    from google.oauth2 import service_account
    from datetime import datetime

    SHEET_ID = "YOUR_SHEET_ID_HERE"
    creds = service_account.Credentials.from_service_account_file(
        '/path/to/service-account.json',
        scopes=['https://www.googleapis.com/auth/drive.readonly']
    )
    drive = build('drive', 'v3', credentials=creds)
    file = drive.files().get(fileId=SHEET_ID, fields='modifiedTime').execute()
    modified = datetime.fromisoformat(file['modifiedTime'].replace('Z', '+00:00'))
    age_minutes = (datetime.now().astimezone() - modified).seconds // 60

    if age_minutes < 60:
        print(f"✓ Sheet updated {age_minutes} minutes ago")
    else:
        print(f"⚠  Sheet last updated {age_minutes} minutes ago — may not have updated")
except ImportError:
    print("⚠  google-api-python-client not installed — manual check required")
EOF
```

---

## XML Sitemap Export

SF can generate an XML sitemap from a crawl.

```bash
DISPLAY=:99 ScreamingFrogSEOSpider \
  --headless \
  --crawl https://www.cars24.com/new-cars/ \
  --max-urls 500 \
  --output-folder /tmp/sf-sitemap-test \
  --overwrite \
  --save-sitemap

# Validate the generated sitemap
python3 << 'EOF'
import xml.etree.ElementTree as ET
import os

sitemap_path = '/tmp/sf-sitemap-test/sitemap.xml'
if not os.path.exists(sitemap_path):
    print("✗ sitemap.xml not found")
    exit()

try:
    tree = ET.parse(sitemap_path)
    root = tree.getroot()
    ns = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
    urls = root.findall('.//sm:url/sm:loc', ns)
    print(f"✓ Valid XML sitemap with {len(urls)} URLs")
    print("Sample URLs:")
    for url in urls[:5]:
        print(f"  {url.text}")
except ET.ParseError as e:
    print(f"✗ Invalid XML: {e}")
EOF
```

---

## Crawl File (.crawl)

Saving the crawl file allows re-opening in SF GUI for manual analysis.

```bash
# --save-crawl flag saves a .crawl file alongside CSVs
DISPLAY=:99 ScreamingFrogSEOSpider \
  --headless \
  --crawl https://www.cars24.com/new-cars/ \
  --max-urls 200 \
  --output-folder /tmp/sf-with-crawl \
  --overwrite \
  --save-crawl

ls -lh /tmp/sf-with-crawl/*.crawl
# Should show a .crawl file
```

---

## Output Naming Best Practice for Cars24

```bash
#!/bin/bash
# Recommended naming convention

DATE=$(date +%Y%m%d)
PROPERTY="cars24-new-cars"
OUTPUT_BASE="/data/seo-audits"

OUTPUT_DIR="$OUTPUT_BASE/$PROPERTY-$DATE"
mkdir -p "$OUTPUT_DIR"

DISPLAY=:99 ScreamingFrogSEOSpider \
  --headless \
  --config /etc/screaming-frog/cars24-production.seospiderconfig \
  --crawl https://www.cars24.com/new-cars/ \
  --max-urls 1000 \
  --output-folder "$OUTPUT_DIR" \
  --save-crawl \
  --timestamped-output \
  2>&1 | tee "$OUTPUT_BASE/logs/$PROPERTY-$DATE.log"

echo "Audit complete: $OUTPUT_DIR"
ls -la "$OUTPUT_DIR"
```
