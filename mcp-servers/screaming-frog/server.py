#!/usr/bin/env python3
"""
Screaming Frog SEO Spider MCP Server
Provides tools to interact with the Screaming Frog SEO Spider application.
"""

import asyncio
import datetime
import json
import os
import re
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

SF_APP = "/Applications/Screaming Frog SEO Spider.app/Contents/MacOS/ScreamingFrogSEOSpiderLauncher"
SF_DATA_DIR = os.path.expanduser("~/.ScreamingFrogSEOSpider")
PROJECT_INSTANCE_DIR = os.path.join(SF_DATA_DIR, "ProjectInstanceData")

app = Server("screaming-frog")


def _get_crawl_url(project_path: str) -> str:
    """Extract the crawl URL from a project's spiderconfig."""
    sc_path = os.path.join(project_path, "serialised_data", "spiderconfig")
    if not os.path.exists(sc_path):
        return ""
    try:
        with open(sc_path, "rb") as f:
            data = f.read()
        text = data.decode("utf-8", errors="ignore")
        urls = re.findall(r"https?://[a-zA-Z0-9._/%-]+", text)
        # Clean up URLs (remove trailing artifact chars)
        clean_urls = []
        for u in urls:
            u = u.rstrip("t")  # strip trailing 't' artifact from binary encoding
            if u and not u.endswith(".xml"):
                clean_urls.append(u)
            elif u:
                clean_urls.append(u)
        return clean_urls[0] if clean_urls else ""
    except Exception:
        return ""


def _get_url_count(project_path: str) -> int:
    """Estimate URL count from spider stats."""
    stats_path = os.path.join(project_path, "serialised_data", "spider_stats")
    if not os.path.exists(stats_path):
        return 0
    try:
        size = os.path.getsize(stats_path)
        # Rough estimate based on file size
        return max(0, size // 50)
    except Exception:
        return 0


def _get_crawl_name(project_path: str, db_id: str) -> str:
    """Try to derive a crawl name from the task name file or URL."""
    # Check for task name
    tasks_dir = os.path.join(SF_DATA_DIR, "tasks")
    # Use URL as name
    url = _get_crawl_url(project_path)
    if url:
        # Clean up the URL for display
        name = re.sub(r"https?://", "", url).rstrip("/")
        return name
    return db_id[:8]


def list_all_crawls() -> list[dict]:
    """List all saved crawls from the Screaming Frog database directory."""
    crawls = []
    if not os.path.exists(PROJECT_INSTANCE_DIR):
        return crawls

    for db_id in os.listdir(PROJECT_INSTANCE_DIR):
        proj_path = os.path.join(PROJECT_INSTANCE_DIR, db_id)
        if not os.path.isdir(proj_path):
            continue

        sd = os.path.join(proj_path, "serialised_data")
        if not os.path.exists(sd):
            continue

        sc_path = os.path.join(sd, "spiderconfig")
        if not os.path.exists(sc_path):
            continue

        try:
            mtime = os.path.getmtime(sc_path)
            modified = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
            url = _get_crawl_url(proj_path)
            url_count = _get_url_count(proj_path)
            percent_complete = 100  # Saved crawls are complete

            crawls.append({
                "db_id": db_id,
                "name": _get_crawl_name(proj_path, db_id),
                "url": url,
                "url_count": url_count,
                "percent_complete": percent_complete,
                "modified": modified,
            })
        except Exception:
            continue

    # Sort by modified date descending
    crawls.sort(key=lambda x: x["modified"], reverse=True)
    return crawls


def export_crawl_data(db_id: str, export_tabs: str = "Internal:All", output_dir: str = None) -> dict:
    """Export crawl data using the Screaming Frog CLI."""
    if output_dir is None:
        output_dir = tempfile.mkdtemp(prefix=f"sf_export_{db_id[:8]}_")

    cmd = [
        SF_APP,
        "--load-crawl", db_id,
        "--headless",
        "--output-folder", output_dir,
        "--export-tabs", export_tabs,
        "--overwrite",
        "--export-format", "csv",
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
        )
        return {
            "success": result.returncode == 0,
            "output_dir": output_dir,
            "stdout": result.stdout[-2000:] if result.stdout else "",
            "stderr": result.stderr[-2000:] if result.stderr else "",
            "return_code": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Export timed out after 300 seconds", "output_dir": output_dir}
    except Exception as e:
        return {"success": False, "error": str(e), "output_dir": output_dir}


def read_exported_data(output_dir: str, filename_pattern: str = None) -> dict:
    """Read exported CSV files from the output directory."""
    if not os.path.exists(output_dir):
        return {"error": f"Output directory not found: {output_dir}", "files": []}

    files = []
    for f in sorted(os.listdir(output_dir)):
        if not f.endswith(".csv"):
            continue
        if filename_pattern and filename_pattern.lower() not in f.lower():
            continue
        fpath = os.path.join(output_dir, f)
        try:
            with open(fpath, "r", encoding="utf-8", errors="replace") as fp:
                content = fp.read()
            lines = content.strip().split("\n")
            files.append({
                "filename": f,
                "rows": len(lines) - 1,  # subtract header
                "size_bytes": os.path.getsize(fpath),
                "preview": "\n".join(lines[:6]),  # header + first 5 rows
            })
        except Exception as e:
            files.append({"filename": f, "error": str(e)})

    return {"output_dir": output_dir, "files": files, "total_files": len(files)}


def start_crawl(url: str, task_name: str = None, save: bool = True,
                export_tabs: str = None, output_dir: str = None) -> dict:
    """Start a new crawl using the Screaming Frog CLI."""
    cmd = [SF_APP, "--crawl", url, "--headless"]

    if task_name:
        cmd.extend(["--task-name", task_name])
    if save:
        cmd.append("--save-crawl")
    if export_tabs and output_dir:
        cmd.extend([
            "--export-tabs", export_tabs,
            "--output-folder", output_dir,
            "--export-format", "csv",
            "--overwrite",
        ])

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return {
            "success": True,
            "pid": proc.pid,
            "message": f"Crawl started for {url} (PID: {proc.pid})",
            "cmd": " ".join(cmd),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def check_sf_status() -> dict:
    """Check if Screaming Frog is installed and get version info."""
    if not os.path.exists(SF_APP):
        return {"installed": False, "error": "Screaming Frog not found at expected path"}

    try:
        result = subprocess.run(
            [SF_APP, "--help"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        version_match = re.search(r"version[:\s]+([0-9.]+)", result.stdout + result.stderr, re.IGNORECASE)
        version = version_match.group(1) if version_match else "unknown"

        crawl_count = len([
            d for d in os.listdir(PROJECT_INSTANCE_DIR)
            if os.path.isdir(os.path.join(PROJECT_INSTANCE_DIR, d))
            and os.path.exists(os.path.join(PROJECT_INSTANCE_DIR, d, "serialised_data", "spiderconfig"))
        ]) if os.path.exists(PROJECT_INSTANCE_DIR) else 0

        return {
            "installed": True,
            "app_path": SF_APP,
            "data_dir": SF_DATA_DIR,
            "saved_crawls": crawl_count,
            "version": version,
        }
    except Exception as e:
        return {"installed": True, "app_path": SF_APP, "error": str(e)}


# ── Tool definitions ──────────────────────────────────────────────────────────

@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="list_crawls",
            description="List all saved crawls from the Screaming Frog database. Returns crawl ID, URL, URL count, and last modified date.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="export_crawl",
            description=(
                "Export crawl data from a saved Screaming Frog crawl using its database ID. "
                "Returns the output directory path where CSV files are saved."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "db_id": {
                        "type": "string",
                        "description": "The database ID (UUID) of the crawl to export",
                    },
                    "export_tabs": {
                        "type": "string",
                        "description": (
                            "Comma-separated list of tabs to export in 'Tab:Filter' format. "
                            "E.g. 'Internal:All,Response Codes:3xx,Page Titles:All'. "
                            "Defaults to 'Internal:All'."
                        ),
                        "default": "Internal:All",
                    },
                    "output_dir": {
                        "type": "string",
                        "description": "Directory to save exported CSV files. Defaults to a temp directory.",
                    },
                },
                "required": ["db_id"],
            },
        ),
        Tool(
            name="read_crawl_data",
            description="Read exported CSV files from a crawl export output directory.",
            inputSchema={
                "type": "object",
                "properties": {
                    "output_dir": {
                        "type": "string",
                        "description": "The output directory from an export_crawl call",
                    },
                    "filename_pattern": {
                        "type": "string",
                        "description": "Optional filter to only return files matching this pattern",
                    },
                },
                "required": ["output_dir"],
            },
        ),
        Tool(
            name="crawl_site",
            description="Start a new Screaming Frog crawl of a website URL.",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL to crawl",
                    },
                    "task_name": {
                        "type": "string",
                        "description": "Optional name for this crawl task",
                    },
                    "save": {
                        "type": "boolean",
                        "description": "Whether to save the crawl to the database (default: true)",
                        "default": True,
                    },
                    "export_tabs": {
                        "type": "string",
                        "description": "Optionally export specific tabs after crawl completes",
                    },
                    "output_dir": {
                        "type": "string",
                        "description": "Output directory for exports (required if export_tabs is set)",
                    },
                },
                "required": ["url"],
            },
        ),
        Tool(
            name="crawl_status",
            description="Check if a Screaming Frog crawl process is currently running.",
            inputSchema={
                "type": "object",
                "properties": {
                    "pid": {
                        "type": "integer",
                        "description": "Optional PID of the crawl process to check",
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="sf_check",
            description="Check if Screaming Frog SEO Spider is installed and accessible.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    if name == "list_crawls":
        crawls = list_all_crawls()
        result = {
            "total_crawls": len(crawls),
            "crawls": crawls,
        }
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "export_crawl":
        db_id = arguments["db_id"]
        export_tabs = arguments.get("export_tabs", "Internal:All")
        output_dir = arguments.get("output_dir")
        result = export_crawl_data(db_id, export_tabs, output_dir)
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "read_crawl_data":
        output_dir = arguments["output_dir"]
        filename_pattern = arguments.get("filename_pattern")
        result = read_exported_data(output_dir, filename_pattern)
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "crawl_site":
        url = arguments["url"]
        task_name = arguments.get("task_name")
        save = arguments.get("save", True)
        export_tabs = arguments.get("export_tabs")
        output_dir = arguments.get("output_dir")
        result = start_crawl(url, task_name, save, export_tabs, output_dir)
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "crawl_status":
        pid = arguments.get("pid")
        if pid:
            try:
                os.kill(pid, 0)
                running = True
            except OSError:
                running = False
            result = {"pid": pid, "running": running}
        else:
            # Check if any SF process is running
            try:
                ps = subprocess.run(
                    ["pgrep", "-f", "ScreamingFrogSEOSpider"],
                    capture_output=True, text=True
                )
                pids = [int(p) for p in ps.stdout.strip().split() if p.strip()]
                result = {"running": len(pids) > 0, "pids": pids}
            except Exception as e:
                result = {"error": str(e)}
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "sf_check":
        result = check_sf_status()
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    else:
        return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
