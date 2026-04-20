# Crawl Tests — Full CLI Flag Reference

## macOS Notes (confirmed from live diagnostic — 2026-04-04)

**Binary path on macOS (not on PATH by default):**
```bash
SF_JRE="/Applications/Screaming Frog SEO Spider.app/Contents/jre/bin/java"
SF_JAR="/Applications/Screaming Frog SEO Spider.app/Contents/Java/ScreamingFrogSEOSpider.jar"
# Wrapper at ~/.local/bin/ScreamingFrogSEOSpider handles this
```

**Config format:** SF `.seospiderconfig` files are binary Java-serialized objects.
Hand-crafted XML files (including `<settings version="1">` XML) will fail with:
`FATAL - Failed to load config: invalid stream header: 3C3F786D`
→ Only configs saved from the SF GUI work. Use CLI flags instead of `--config` where possible.

**`--max-urls` does NOT exist as a CLI flag.** URL limit must be set in the GUI config.

**Correct export tab names** (verified from `--help export-tabs`):
```
Internal:All            Page Titles:All         Meta Description:All
Response Codes:All      H1:All                  H2:All
Canonicals:All          Images:All              Images:Missing Alt Text
Structured Data:All     Directives:All          Hreflang:All
Sitemaps:All            Custom Extraction:All   Page Speed:All
```
Note: "Canonical URL" is WRONG — correct name is "Canonicals"

**JS rendering** is set in spider.config (GUI). If the default config has JS rendering ON,
headless crawls will be very slow (Chromium headless spawns per URL). Disable via:
SF GUI > Configuration > Spider > Rendering > set to "None" > save config.

**GSC auto-connects** from the default spider.config if authenticated via GUI.
The `--use-google-search-console` CLI flag is available for explicit control:
```bash
ScreamingFrogSEOSpider --headless --crawl URL \
  --use-google-search-console "saveduser" "https://www.cars24.com/new-cars/"
```

## Full Headless Command Template

```bash
# macOS — no DISPLAY needed, no --config needed if using default spider.config
ScreamingFrogSEOSpider \
  --headless \
  --crawl https://www.cars24.com/new-cars/ \
  --output-folder /output/cars24-$(date +%Y%m%d) \
  --overwrite \
  --timestamped-output \
  --save-crawl \
  --export-tabs "Internal:All,Response Codes:All,Page Titles:All,Meta Description:All,H1:All,Canonicals:All,Directives:All,Images:Missing Alt Text,Structured Data:All" \
  2>&1 | tee /logs/sf-crawl-$(date +%Y%m%d).log

# Linux — requires DISPLAY=:99 and Xvfb
DISPLAY=:99 ScreamingFrogSEOSpider \
  --headless \
  --config /path/to/gui-saved-config.seospiderconfig \
  --crawl https://www.cars24.com/new-cars/ \
  --output-folder /output/cars24-$(date +%Y%m%d) \
  --overwrite \
  --export-tabs "Internal:All,Response Codes:All,Page Titles:All,Meta Description:All,H1:All,Canonicals:All,Directives:All,Images:Missing Alt Text,Structured Data:All" \
  2>&1 | tee /logs/sf-crawl-$(date +%Y%m%d).log
```

## Crawl Mode Tests

### Test C1 — Minimal single URL crawl
```bash
DISPLAY=:99 ScreamingFrogSEOSpider \
  --headless \
  --crawl https://example.com \
  --max-urls 1 \
  --output-folder /tmp/sf-test-c1 \
  --overwrite
echo "C1 exit: $?"
```

### Test C2 — Depth-limited crawl
```bash
DISPLAY=:99 ScreamingFrogSEOSpider \
  --headless \
  --crawl https://www.cars24.com/new-cars/ \
  --crawl-depth 2 \
  --max-urls 50 \
  --output-folder /tmp/sf-test-c2 \
  --overwrite
# Verify: URLs in output should be within 2 hops of start URL
```

### Test C3 — URL list mode
```bash
# Create test URL list
cat > /tmp/test-urls.txt << 'EOF'
https://www.cars24.com/new-cars/
https://www.cars24.com/new-cars/tata/
https://www.cars24.com/new-cars/maruti-suzuki/
EOF

DISPLAY=:99 ScreamingFrogSEOSpider \
  --headless \
  --crawl-list /tmp/test-urls.txt \
  --output-folder /tmp/sf-test-c3 \
  --overwrite
# Verify: exactly 3 URLs in internal_all.csv
```

### Test C4 — Sitemap crawl mode
```bash
DISPLAY=:99 ScreamingFrogSEOSpider \
  --headless \
  --crawl-sitemap https://www.cars24.com/sitemap.xml \
  --max-urls 100 \
  --output-folder /tmp/sf-test-c4 \
  --overwrite
```

### Test C5 — Robots.txt respect
```bash
# Crawl with robots respect ON
DISPLAY=:99 ScreamingFrogSEOSpider \
  --headless \
  --crawl https://www.cars24.com/new-cars/ \
  --respect-robots-txt true \
  --max-urls 50 \
  --output-folder /tmp/sf-test-c5-robots-on \
  --overwrite

# Count blocked URLs
grep "Blocked by robots.txt" /tmp/sf-test-c5-robots-on/*.csv | wc -l
```

### Test C6 — JavaScript rendering
```bash
# JS rendering is set via config, not CLI flag directly
# Verify via custom extraction of JS-rendered element

DISPLAY=:99 ScreamingFrogSEOSpider \
  --headless \
  --config /path/to/config-with-js.seospiderconfig \
  --crawl https://www.cars24.com/new-cars/tata/nexon/ \
  --max-urls 5 \
  --output-folder /tmp/sf-test-c6 \
  --overwrite

# Check if JS-rendered price is in custom extraction column
grep -i "price" /tmp/sf-test-c6/internal_html.csv | head -5
```

### Test C7 — Custom user agent
```bash
DISPLAY=:99 ScreamingFrogSEOSpider \
  --headless \
  --crawl https://httpbin.org/user-agent \
  --max-urls 1 \
  --user-agent "Cars24SEOAudit/1.0 (+https://www.cars24.com)" \
  --output-folder /tmp/sf-test-c7 \
  --overwrite

# Verify user agent was sent (httpbin reflects it back)
cat /tmp/sf-test-c7/internal_html.csv
```

## Key CLI Flags Reference

### Crawl Control
| Flag | Values | Notes |
|------|--------|-------|
| `--headless` | (flag) | Required for headless mode |
| `--crawl <url>` | URL | Start URL for spider mode |
| `--crawl-list <file>` | Path | One URL per line |
| `--crawl-sitemap <url>` | URL | Crawl from XML sitemap |
| `--max-urls <n>` | Integer | Hard cap on URLs crawled |
| `--crawl-depth <n>` | Integer | Max hops from start URL |
| `--crawl-delay <ms>` | Milliseconds | Delay between requests |
| `--threads <n>` | Integer | Concurrent threads (default 5) |

### Output Control
| Flag | Values | Notes |
|------|--------|-------|
| `--output-folder <path>` | Absolute path | Must be absolute for cron |
| `--overwrite` | (flag) | Overwrite existing output |
| `--timestamped-output` | (flag) | Appends timestamp to folder |
| `--save-crawl` | (flag) | Saves .crawl file for later opening |
| `--export-tabs <tabs>` | Comma-separated | See export format below |
| `--save-report <name>` | String | Custom report name |

### Export Tab Names (exact strings)
```
Internal:All
Internal:HTML
Internal:JavaScript
Internal:CSS
Response Codes:All
Response Codes:Success (2xx)
Response Codes:Redirection (3xx)
Response Codes:Client Error (4xx)
Response Codes:Server Error (5xx)
Page Titles:All
Page Titles:Missing
Page Titles:Duplicate
Meta Description:All
Meta Description:Missing
H1:All
H1:Missing
H1:Duplicate
H2:All
Canonical URL:All
Directives:All
Images:All
Images:Missing Alt Text
Images:Alt Text Over 100 Characters
Structured Data:All
Hreflang:All
Links:All Inlinks
Links:All Outlinks
Sitemaps:All
Page Speed:All
```

## Common Crawl Failures & Fixes

### SF starts but produces empty output
- Check `$DISPLAY` is set before running
- Check license (free tier hits 500 URL cap silently in some versions)
- Check output folder permissions: `mkdir -p /output && chmod 777 /output`

### Crawl hangs indefinitely
- Add `--max-urls` cap
- Add timeout wrapper: `timeout 3600 ScreamingFrogSEOSpider ...`
- Check for redirect loops: `--max-redirects 3`

### JS rendering not working
- Ensure Chromium/Chrome installed: `google-chrome --version`
- SF bundles Chromium but sometimes system Chrome interferes
- Check SF logs: `~/.ScreamingFrogSEOSpider/logs/`

### 403 errors on Cars24
- Cars24 blocks default SF user agent
- Set custom UA that mimics Googlebot or real browser
- Add `--cookies` flag if session required
