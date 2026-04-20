#!/bin/bash
# =============================================================================
# SF Headless Diagnostic Script — Cars24 SEO
# Run this on any server to get a full health report of your SF installation
# Usage: bash sf-diagnose.sh [start-url] [output-dir] [config-path]
# Example: bash sf-diagnose.sh https://www.cars24.com/new-cars/ /tmp/sf-diag /etc/sf/cars24.seospiderconfig
# =============================================================================

set -uo pipefail

START_URL="${1:-https://example.com}"
OUTPUT_DIR="${2:-/tmp/sf-diagnostic-$(date +%Y%m%d_%H%M)}"
CONFIG_PATH="${3:-}"

PASS=0
FAIL=0
WARN=0
REPORT=""

pass() { echo "✓ PASS: $1"; REPORT+="  ✓ $1\n"; ((PASS++)); }
fail() { echo "✗ FAIL: $1"; REPORT+="  ✗ $1\n"; ((FAIL++)); }
warn() { echo "⚠  WARN: $1"; REPORT+="  ⚠  $1\n"; ((WARN++)); }
section() { echo ""; echo "─── $1 ───"; REPORT+="\n$1\n"; }

mkdir -p "$OUTPUT_DIR"

# ─────────────────────────────────────────────────────────────────────────────
section "PHASE 0 — ENVIRONMENT"
# ─────────────────────────────────────────────────────────────────────────────

echo "OS: $(uname -a)"
echo "Date: $(date)"
echo "User: $(whoami)"

# Java check
if java -version 2>&1 | grep -qE "version \"(1[1-9]|[2-9][0-9])"; then
  JAVA_VER=$(java -version 2>&1 | head -1)
  pass "Java version OK: $JAVA_VER"
else
  fail "Java 11+ not found. Install: sudo apt install openjdk-17-jre-headless"
fi

# SF binary
SF_BIN=$(which ScreamingFrogSEOSpider 2>/dev/null || \
         find /usr /opt /home -name "ScreamingFrogSEOSpider" 2>/dev/null | head -1)
if [ -n "$SF_BIN" ]; then
  pass "SF binary found: $SF_BIN"
else
  fail "SF binary not found. Install Screaming Frog from screamingfrog.co.uk"
  echo "FATAL: Cannot continue without SF binary. Exiting."
  exit 1
fi

# SF version
SF_VERSION=$($SF_BIN --version 2>&1)
echo "SF Version: $SF_VERSION"

# Display server
export DISPLAY="${DISPLAY:-:99}"
if [ -n "$DISPLAY" ]; then
  pass "DISPLAY set: $DISPLAY"
else
  fail "DISPLAY not set. Run: export DISPLAY=:99 && Xvfb :99 -screen 0 1024x768x24 &"
fi

# Xvfb
if pgrep -x Xvfb > /dev/null; then
  pass "Xvfb running"
elif which Xvfb > /dev/null 2>&1; then
  warn "Xvfb installed but not running. Starting it..."
  Xvfb :99 -screen 0 1024x768x24 -ac &
  sleep 2
  pgrep -x Xvfb > /dev/null && pass "Xvfb started successfully" || fail "Xvfb failed to start"
else
  fail "Xvfb not installed. Run: sudo apt install xvfb"
fi

# License
LICENSE_INFO=$($SF_BIN --license-info 2>&1)
if echo "$LICENSE_INFO" | grep -qi "licensed\|enterprise\|paid"; then
  pass "SF Licensed (full crawl capability)"
elif echo "$LICENSE_INFO" | grep -qi "free\|trial\|500"; then
  warn "SF Free tier — crawl limit: 500 URLs. Activate license for full crawls."
else
  warn "License status unclear: $LICENSE_INFO"
fi

# RAM
RAM_GB=$(free -g | awk '/^Mem:/{print $2}')
if [ "$RAM_GB" -ge 4 ]; then
  pass "RAM: ${RAM_GB}GB (sufficient)"
elif [ "$RAM_GB" -ge 2 ]; then
  warn "RAM: ${RAM_GB}GB (minimum — large crawls may fail)"
else
  fail "RAM: ${RAM_GB}GB (insufficient for large crawls)"
fi

# Disk space
DISK_FREE=$(df -BG "$OUTPUT_DIR" | awk 'NR==2{print $4}' | tr -d 'G')
if [ "$DISK_FREE" -ge 5 ]; then
  pass "Disk space: ${DISK_FREE}GB free"
else
  warn "Disk space: ${DISK_FREE}GB free (may be insufficient for large exports)"
fi

# ─────────────────────────────────────────────────────────────────────────────
section "PHASE 1 — SMOKE TEST CRAWL"
# ─────────────────────────────────────────────────────────────────────────────

SMOKE_DIR="$OUTPUT_DIR/smoke-test"
mkdir -p "$SMOKE_DIR"

echo "Running minimal crawl on https://example.com ..."

DISPLAY=:99 timeout 120 $SF_BIN \
  --headless \
  --crawl https://example.com \
  --max-urls 3 \
  --output-folder "$SMOKE_DIR" \
  --overwrite \
  > "$SMOKE_DIR/smoke.log" 2>&1
SMOKE_EXIT=$?

if [ $SMOKE_EXIT -eq 0 ]; then
  pass "Smoke test crawl: exit 0"
else
  fail "Smoke test crawl: exit $SMOKE_EXIT (check $SMOKE_DIR/smoke.log)"
  cat "$SMOKE_DIR/smoke.log" | tail -20
fi

CSV_COUNT=$(ls "$SMOKE_DIR"/*.csv 2>/dev/null | wc -l)
if [ "$CSV_COUNT" -gt 0 ]; then
  pass "Output CSVs produced: $CSV_COUNT files"
  ls "$SMOKE_DIR"/*.csv
else
  fail "No CSV output produced (check license cap or display issue)"
fi

# ─────────────────────────────────────────────────────────────────────────────
section "PHASE 2 — TARGET URL CRAWL"
# ─────────────────────────────────────────────────────────────────────────────

TARGET_DIR="$OUTPUT_DIR/target-crawl"
mkdir -p "$TARGET_DIR"

echo "Running limited crawl on $START_URL ..."

SF_ARGS=(
  --headless
  --crawl "$START_URL"
  --max-urls 20
  --output-folder "$TARGET_DIR"
  --overwrite
  --export-tabs "Internal:All,Response Codes:All,Page Titles:All,H1:All,Canonical URL:All,Images:Missing Alt Text"
)

# Add config if provided
if [ -n "$CONFIG_PATH" ] && [ -f "$CONFIG_PATH" ]; then
  SF_ARGS+=(--config "$CONFIG_PATH")
  pass "Config file provided: $CONFIG_PATH"
elif [ -n "$CONFIG_PATH" ]; then
  fail "Config file not found: $CONFIG_PATH"
fi

DISPLAY=:99 timeout 300 $SF_BIN "${SF_ARGS[@]}" \
  > "$TARGET_DIR/crawl.log" 2>&1
TARGET_EXIT=$?

if [ $TARGET_EXIT -eq 0 ]; then
  pass "Target crawl: exit 0"
else
  fail "Target crawl: exit $TARGET_EXIT"
  cat "$TARGET_DIR/crawl.log" | grep -i "error\|exception\|fail" | head -10
fi

# Check each expected CSV
for csv in "internal_all.csv" "internal_html.csv" "response_codes_all.csv" \
           "page_titles_all.csv" "h1_all.csv" "canonical_url_all.csv"; do
  if [ -f "$TARGET_DIR/$csv" ]; then
    ROWS=$(($(wc -l < "$TARGET_DIR/$csv") - 1))
    if [ "$ROWS" -gt 0 ]; then
      pass "Export: $csv ($ROWS URLs)"
    else
      warn "Export: $csv is empty (0 data rows)"
    fi
  else
    fail "Export missing: $csv"
  fi
done

# Check for 4xx/5xx on target site
if [ -f "$TARGET_DIR/response_codes_all.csv" ]; then
  ERRORS=$(tail -n +2 "$TARGET_DIR/response_codes_all.csv" | \
    awk -F',' '$3 ~ /^[45]/' | wc -l)
  [ "$ERRORS" -gt 0 ] && warn "4xx/5xx errors found: $ERRORS" || \
    pass "No 4xx/5xx errors in limited crawl"
fi

# ─────────────────────────────────────────────────────────────────────────────
section "PHASE 3 — API INTEGRATION CHECKS"
# ─────────────────────────────────────────────────────────────────────────────

if [ -f "$TARGET_DIR/internal_html.csv" ]; then
  HEADER=$(head -1 "$TARGET_DIR/internal_html.csv")

  echo "$HEADER" | grep -qi "impression\|clicks\|position" && \
    pass "GSC integration: columns present" || \
    warn "GSC integration: columns not found (may need config with GSC enabled)"

  echo "$HEADER" | grep -qi "session\|engaged" && \
    pass "GA4 integration: columns present" || \
    warn "GA4 integration: columns not found (may need config with GA4 enabled)"

  echo "$HEADER" | grep -qi "performance score\|lcp\|cls" && \
    pass "PageSpeed integration: columns present" || \
    warn "PageSpeed integration: columns not found (needs PSI API key in config)"

  echo "$HEADER" | grep -qi "trust flow\|citation flow" && \
    pass "Majestic integration: columns present" || \
    warn "Majestic integration: not configured (optional)"
fi

# ─────────────────────────────────────────────────────────────────────────────
section "PHASE 4 — CUSTOM EXTRACTION CHECK"
# ─────────────────────────────────────────────────────────────────────────────

EXTRACT_FILES=$(ls "$TARGET_DIR"/custom_extraction*.csv 2>/dev/null | wc -l)
if [ "$EXTRACT_FILES" -gt 0 ]; then
  pass "Custom extraction: $EXTRACT_FILES extraction file(s) found"
  for f in "$TARGET_DIR"/custom_extraction*.csv; do
    ROWS=$(($(wc -l < "$f") - 1))
    [ "$ROWS" -gt 0 ] && pass "  $(basename $f): $ROWS rows" || \
      warn "  $(basename $f): empty (check XPath/CSS selectors)"
  done
else
  warn "Custom extraction: no files found (add extraction rules to config if needed)"
fi

# ─────────────────────────────────────────────────────────────────────────────
section "PHASE 5 — CRON/SCHEDULING CHECK"
# ─────────────────────────────────────────────────────────────────────────────

# Check if DISPLAY is in environment (not just exported)
env | grep -q "DISPLAY" && pass "DISPLAY in environment" || \
  warn "DISPLAY not in environment (will fail in cron — add to crontab)"

# Check for wrapper script
[ -f "/usr/local/bin/run-cars24-audit.sh" ] && \
  pass "Wrapper script found: /usr/local/bin/run-cars24-audit.sh" || \
  warn "No wrapper script found — create one from references/scheduling.md"

# Check for lock file mechanism
grep -q "LOCK_FILE" /usr/local/bin/run-cars24-audit.sh 2>/dev/null && \
  pass "Lock file protection in wrapper" || \
  warn "No lock file in wrapper (risk of concurrent crawls)"

# ─────────────────────────────────────────────────────────────────────────────
section "FINAL REPORT"
# ─────────────────────────────────────────────────────────────────────────────

echo ""
echo "═══════════════════════════════════════════════════"
echo "SCREAMING FROG HEADLESS DIAGNOSTIC REPORT"
echo "Date: $(date)"
echo "Target: $START_URL"
echo "═══════════════════════════════════════════════════"
echo ""
echo "RESULTS: $PASS passed | $FAIL failed | $WARN warnings"
echo ""
printf "$REPORT"
echo ""

if [ "$FAIL" -gt 0 ]; then
  echo "✗ BLOCKING ISSUES: $FAIL failures must be fixed"
  exit 1
elif [ "$WARN" -gt 0 ]; then
  echo "⚠  Some warnings — review above. Core functionality working."
  exit 0
else
  echo "✓ All checks passed. SF headless is working correctly."
  exit 0
fi
