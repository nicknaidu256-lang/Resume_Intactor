"""Lightweight local dashboard UI served over HTTP."""

from __future__ import annotations

import html
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Dict, List

from src.tracking.tracker import get_stats, get_recent_jobs


class _DashboardHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        stats = get_stats()
        recent_jobs = get_recent_jobs(limit=15)
        body = _render_dashboard(stats, recent_jobs)
        payload = body.encode("utf-8")

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format, *args):
        return


class DashboardApp:
    """Simple dashboard app with a `.run()` entry point."""

    def __init__(self, host: str = "127.0.0.1", port: int = 8080):
        self.host = host
        self.port = port

    def run(self):
        server = ThreadingHTTPServer((self.host, self.port), _DashboardHandler)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            server.server_close()


def create_dashboard() -> DashboardApp:
    """Factory used by the CLI."""
    return DashboardApp()


def _render_dashboard(stats: Dict[str, int], recent_jobs: List[Dict[str, str]]) -> str:
    cards = [
        ("Total Jobs", stats.get("total_jobs", 0)),
        ("Applied", stats.get("applied_jobs", 0)),
        ("Interview", stats.get("interview_jobs", 0)),
        ("Offers", stats.get("offer_jobs", 0)),
    ]

    card_html = "".join(
        f"<div class='card'><div class='label'>{html.escape(label)}</div><div class='value'>{value}</div></div>"
        for label, value in cards
    )

    rows = []
    for job in recent_jobs:
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(job.get('title', '')))}</td>"
            f"<td>{html.escape(str(job.get('company', '')))}</td>"
            f"<td>{html.escape(str(job.get('location', '')))}</td>"
            f"<td>{html.escape(str(job.get('status', 'discovered')))}</td>"
            f"<td>{html.escape(str(job.get('score', '')))}</td>"
            "</tr>"
        )
    if not rows:
        rows.append("<tr><td colspan='5'>No jobs found in data/jobs.db</td></tr>")

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Resume Intactor Dashboard</title>
  <style>
    body {{
      font-family: Arial, sans-serif;
      margin: 0;
      background: #f5f7fb;
      color: #1f2937;
    }}
    .wrap {{
      max-width: 1100px;
      margin: 0 auto;
      padding: 24px;
    }}
    h1 {{
      margin: 0 0 8px;
    }}
    .muted {{
      color: #6b7280;
      margin-bottom: 24px;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 16px;
      margin-bottom: 24px;
    }}
    .card {{
      background: white;
      border-radius: 12px;
      padding: 18px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    }}
    .label {{
      font-size: 13px;
      color: #6b7280;
      margin-bottom: 8px;
    }}
    .value {{
      font-size: 28px;
      font-weight: 700;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      background: white;
      border-radius: 12px;
      overflow: hidden;
      box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    }}
    th, td {{
      padding: 12px 14px;
      border-bottom: 1px solid #e5e7eb;
      text-align: left;
      vertical-align: top;
    }}
    th {{
      background: #f9fafb;
      font-size: 13px;
      color: #374151;
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <h1>Application Dashboard</h1>
    <div class="muted">Reading live data from <code>data/jobs.db</code></div>
    <div class="grid">{card_html}</div>
    <table>
      <thead>
        <tr>
          <th>Title</th>
          <th>Company</th>
          <th>Location</th>
          <th>Status</th>
          <th>Score</th>
        </tr>
      </thead>
      <tbody>
        {''.join(rows)}
      </tbody>
    </table>
  </div>
</body>
</html>"""
