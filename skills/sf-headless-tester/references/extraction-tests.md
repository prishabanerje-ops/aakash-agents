# Custom Extraction Tests

Custom extraction must be saved in the `.seospiderconfig` file — it cannot
be set via CLI flags at runtime. The config must be pre-built with extraction
rules, then referenced with `--config`.

---

## How Custom Extraction Works in Headless Mode

1. Build extraction rules in SF GUI (Configuration > Custom > Extraction)
2. Save config: File > Save Config As > `cars24-extraction.seospiderconfig`
3. Transfer config to headless server
4. Reference in CLI: `--config /path/to/cars24-extraction.seospiderconfig`
5. Output CSV will contain custom extraction columns

---

## Cars24-Specific Extraction Rules

### Rule Set 1 — SEO Elements

| Slot | Name | Type | Expression |
|------|------|------|------------|
| 1 | H1 Text | XPath | `//h1[1]/text()` |
| 2 | Schema Type | XPath | `//script[@type='application/ld+json'][1]` |
| 3 | Canonical URL | XPath | `//link[@rel='canonical']/@href` |
| 4 | Meta Robots | XPath | `//meta[@name='robots']/@content` |
| 5 | OG Title | XPath | `//meta[@property='og:title']/@content` |

### Rule Set 2 — Cars24 Specific

| Slot | Name | Type | Expression |
|------|------|------|------------|
| 1 | Car Price | XPath | `//*[contains(@class,'price')]//text()` |
| 2 | Car Model Name | XPath | `//h1[contains(@class,'model')]/text()` |
| 3 | Used Car CTA | CSS | `.cpo-section a` |
| 4 | Schema JSON-LD | XPath | `//script[@type='application/ld+json']` |

---

## Test X1 — XPath Extraction

```bash
# Step 1: Verify config has extraction rules
cat /path/to/config.seospiderconfig | grep -A5 "customExtraction"

# Step 2: Run crawl
DISPLAY=:99 ScreamingFrogSEOSpider \
  --headless \
  --config /path/to/config-with-extraction.seospiderconfig \
  --crawl https://www.cars24.com/new-cars/tata/nexon/ \
  --max-urls 10 \
  --output-folder /tmp/sf-extraction-test \
  --overwrite \
  --export-tabs "Custom Extraction:All"

# Step 3: Verify extraction columns and data
head -1 /tmp/sf-extraction-test/*.csv | tr ',' '\n' | grep -i "extract\|custom\|h1\|price"
# Check actual values
csvcut -n /tmp/sf-extraction-test/custom_extraction*.csv 2>/dev/null || \
  awk -F',' 'NR<=3 {print $0}' /tmp/sf-extraction-test/custom_extraction*.csv
```

**Pass:** Custom extraction columns present, non-empty values on crawled URLs
**Fail — column missing:** Extraction rules not in config or wrong config loaded
**Fail — column empty:** XPath wrong, or JS rendering needed but disabled

---

## Test X2 — Schema JSON-LD Extraction

```bash
# Special config needed: extracts full JSON-LD block
# Rule: XPath = //script[@type='application/ld+json']
# Type: Extract Text

DISPLAY=:99 ScreamingFrogSEOSpider \
  --headless \
  --config /path/to/config-schema-extraction.seospiderconfig \
  --crawl https://www.cars24.com/new-cars/tata/nexon/ \
  --max-urls 5 \
  --output-folder /tmp/sf-schema-test \
  --overwrite

# Validate extracted JSON-LD
python3 << 'EOF'
import csv, json, sys

with open('/tmp/sf-schema-test/custom_extraction_1.csv') as f:
    reader = csv.DictReader(f)
    for row in reader:
        # Find column with JSON-LD data
        for col, val in row.items():
            if val and val.strip().startswith('{'):
                try:
                    parsed = json.loads(val)
                    print(f"✓ Valid JSON-LD on {row['Address']}: @type={parsed.get('@type','unknown')}")
                except json.JSONDecodeError as e:
                    print(f"✗ Invalid JSON-LD on {row['Address']}: {e}")
EOF
```

---

## Test X3 — JS-Rendered Extraction

Some Cars24 elements are rendered client-side (price, availability).
Test whether extraction captures them when JS rendering is ON.

```bash
# Config A: JS rendering OFF
DISPLAY=:99 ScreamingFrogSEOSpider \
  --headless \
  --config /path/to/config-no-js.seospiderconfig \
  --crawl https://www.cars24.com/new-cars/tata/nexon/ \
  --max-urls 3 \
  --output-folder /tmp/sf-no-js \
  --overwrite

# Config B: JS rendering ON
DISPLAY=:99 ScreamingFrogSEOSpider \
  --headless \
  --config /path/to/config-with-js.seospiderconfig \
  --crawl https://www.cars24.com/new-cars/tata/nexon/ \
  --max-urls 3 \
  --output-folder /tmp/sf-with-js \
  --overwrite

# Compare price extraction column between A and B
echo "=== Without JS ==="
awk -F',' 'NR==2 {print $0}' /tmp/sf-no-js/custom_extraction*.csv 2>/dev/null

echo "=== With JS ==="
awk -F',' 'NR==2 {print $0}' /tmp/sf-with-js/custom_extraction*.csv 2>/dev/null
```

---

## Config Verification Script

```bash
#!/bin/bash
# verify-extraction-config.sh — checks a .seospiderconfig has extraction rules

CONFIG="${1:-/path/to/config.seospiderconfig}"

if [ ! -f "$CONFIG" ]; then
  echo "✗ Config not found: $CONFIG"
  exit 1
fi

# SF configs are XML
RULE_COUNT=$(grep -c "customExtraction" "$CONFIG" 2>/dev/null || echo 0)
JS_ENABLED=$(grep -i "useRenderer\|jsRendering" "$CONFIG" | grep -i "true" | wc -l)

echo "Config: $CONFIG"
echo "Extraction rules found: $RULE_COUNT"
echo "JS rendering enabled: $([ $JS_ENABLED -gt 0 ] && echo YES || echo NO)"

# List extraction expressions
grep -A3 "customExtraction" "$CONFIG" 2>/dev/null | grep -E "xpath|css|regex|expression" | head -10
```

---

## Common Extraction Failures

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| Column missing in export | Rules not in config | Rebuild config with extraction rules |
| Column present but empty | Wrong XPath | Test XPath in browser DevTools first |
| Column empty on JS content | JS rendering off | Enable renderer in config |
| Partial data (some URLs empty) | XPath not universal | Make XPath more flexible with `contains()` |
| Very slow crawl with extraction | JS rendering on + many URLs | Limit `--max-urls` or use URL list mode |
