# Installation & Binary Checks

## Check 1 — Binary exists and is executable

```bash
which ScreamingFrogSEOSpider
# If not found, try common locations:
ls /usr/bin/ScreamingFrogSEOSpider
ls /opt/screamingfrogseospider/ScreamingFrogSEOSpider
ls ~/ScreamingFrogSEOSpider/ScreamingFrogSEOSpider
```

**Fix if missing:**
```bash
# Ubuntu/Debian
wget https://download.screamingfrog.co.uk/products/seo-spider/screamingfrogseospider_21.x_amd64.deb
sudo dpkg -i screamingfrogseospider_21.x_amd64.deb

# Or via apt (if repo configured)
sudo apt-get install screamingfrogseospider
```

## Check 2 — Java version

SF requires **Java 11 or higher**. Java 17 (LTS) recommended.

```bash
java -version 2>&1
# Expected: openjdk version "17.x.x" or "11.x.x"

# If wrong version:
sudo apt install openjdk-17-jre-headless
sudo update-alternatives --config java
```

**Critical:** SF bundles its own JRE on some Linux builds. If system Java
is wrong but SF still works, it's using bundled JRE. Check:
```bash
ls /opt/screamingfrogseospider/jre/bin/java
```

## Check 3 — Display server (Xvfb)

SF uses a GUI toolkit even in headless mode and **requires a virtual display**.
This is the #1 cause of headless failures.

```bash
# Check if DISPLAY is set
echo $DISPLAY
# Should show ":99" or similar — NOT empty

# Check if Xvfb is running
pgrep Xvfb
# Should return a PID

# Start Xvfb if not running
Xvfb :99 -screen 0 1024x768x24 &
export DISPLAY=:99
```

**For systemd/cron reliability, use a proper Xvfb service:**
```bash
# /etc/systemd/system/xvfb.service
[Unit]
Description=Virtual Frame Buffer X Server
After=network.target

[Service]
ExecStart=/usr/bin/Xvfb :99 -screen 0 1024x768x24 -ac +extension GLX +render -noreset
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable xvfb
sudo systemctl start xvfb
```

## Check 4 — License validation

```bash
ScreamingFrogSEOSpider --license-info 2>&1
```

**Free tier limit:** 500 URLs per crawl. If Cars24 crawls silently stop at 500,
this is the cause.

**License file location:** `~/.ScreamingFrogSEOSpider/licence.txt`

```bash
cat ~/.ScreamingFrogSEOSpider/licence.txt
# Should contain your license key
```

**Activate license headlessly:**
```bash
ScreamingFrogSEOSpider --activate-license YOUR-LICENSE-KEY
```

## Check 5 — Config directory

SF stores config, logs, and auth tokens here:
```bash
ls -la ~/.ScreamingFrogSEOSpider/
# Expected dirs: backups/, logs/, user-agents/
# Expected files: licence.txt, (oauth tokens)
```

Permissions must be read/write for the running user:
```bash
chmod 755 ~/.ScreamingFrogSEOSpider/
```

## Check 6 — Minimal smoke test

```bash
DISPLAY=:99 ScreamingFrogSEOSpider \
  --headless \
  --crawl https://httpbin.org/get \
  --max-urls 1 \
  --output-folder /tmp/sf-smoke-test \
  --overwrite \
  2>&1

echo "Exit code: $?"
ls /tmp/sf-smoke-test/
```

**Pass:** exit code 0, output folder contains CSV files
**Fail patterns:**
- `Exception in thread "main"` — Java issue
- `Cannot connect to X11` — Display issue
- `Unable to create output folder` — Permissions issue
- No output but exit 0 — License cap hit or silent config error

## Check 7 — Version compatibility matrix

| SF Version | Min Java | JS Rendering Engine | Notes |
|------------|----------|---------------------|-------|
| 21.x       | Java 11  | Chromium bundled    | Current stable |
| 20.x       | Java 11  | Chromium bundled    | |
| 19.x       | Java 8   | Chromium bundled    | EOL |
| 18.x       | Java 8   | PhantomJS (old)     | EOL — upgrade |

Check current version:
```bash
ScreamingFrogSEOSpider --version
```
