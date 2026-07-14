"""HTML report generator using Jinja2."""

from collections import Counter
from datetime import datetime

from jinja2 import Template

from app.analyzer.base import AnalyzerIssue

_HTML_TEMPLATE = Template(
    """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>CodeGuardian AI — Review Report</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
           background: #f8f9fa; color: #212529; line-height: 1.5; }
    .container { max-width: 1100px; margin: 0 auto; padding: 24px; }
    header { background: linear-gradient(135deg, #1a1a2e, #16213e);
             color: white; padding: 32px 24px; border-radius: 12px; margin-bottom: 24px; }
    header h1 { font-size: 1.8rem; margin-bottom: 8px; }
    header .meta { font-size: 0.9rem; opacity: 0.8; }
    .cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
             gap: 16px; margin-bottom: 24px; }
    .card { background: white; border-radius: 8px; padding: 16px; text-align: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
    .card .count { font-size: 2rem; font-weight: 700; }
    .card .label { font-size: 0.75rem; color: #6c757d; text-transform: uppercase; }
    .critical .count { color: #dc3545; }
    .high .count { color: #fd7e14; }
    .medium .count { color: #ffc107; }
    .low .count { color: #20c997; }
    .info .count { color: #0dcaf0; }
    .section { background: white; border-radius: 8px; padding: 24px;
               box-shadow: 0 2px 8px rgba(0,0,0,0.08); margin-bottom: 16px; }
    .section h2 { font-size: 1.1rem; margin-bottom: 16px; color: #343a40;
                  border-bottom: 2px solid #e9ecef; padding-bottom: 8px; }
    .summary { color: #495057; margin-bottom: 8px; }
    table { width: 100%; border-collapse: collapse; font-size: 0.875rem; }
    th { background: #f8f9fa; text-align: left; padding: 10px 12px;
         font-size: 0.75rem; text-transform: uppercase; color: #6c757d;
         border-bottom: 2px solid #dee2e6; }
    td { padding: 10px 12px; border-bottom: 1px solid #f1f3f5; vertical-align: top; }
    tr:hover td { background: #f8f9fa; }
    .badge { display: inline-block; padding: 2px 8px; border-radius: 12px;
             font-size: 0.7rem; font-weight: 600; text-transform: uppercase; }
    .badge-CRITICAL { background: #dc3545; color: white; }
    .badge-HIGH { background: #fd7e14; color: white; }
    .badge-MEDIUM { background: #ffc107; color: #212529; }
    .badge-LOW { background: #20c997; color: white; }
    .badge-INFO { background: #0dcaf0; color: #212529; }
    .location { font-family: monospace; font-size: 0.8rem; color: #495057; }
    .suggestion { background: #f8f9fa; border-left: 3px solid #20c997;
                  padding: 8px 12px; margin-top: 6px; border-radius: 4px;
                  font-size: 0.8rem; white-space: pre-wrap; font-family: monospace; }
    footer { text-align: center; padding: 24px; color: #6c757d; font-size: 0.8rem; }
    .gate-PASS { color: #20c997; font-weight: 700; }
    .gate-FAIL { color: #dc3545; font-weight: 700; }
    .gate-SKIPPED { color: #6c757d; }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <h1>🛡️ CodeGuardian AI — Code Review Report</h1>
      <div class="meta">
        Review ID: {{ review_id }} &nbsp;|&nbsp;
        Target: {{ target or "code snippet" }} &nbsp;|&nbsp;
        Mode: {{ mode }} &nbsp;|&nbsp;
        Generated: {{ generated_at }}
      </div>
    </header>

    <!-- Severity statistics cards -->
    <div class="cards">
      <div class="card critical">
        <div class="count">{{ counts.CRITICAL }}</div>
        <div class="label">Critical</div>
      </div>
      <div class="card high">
        <div class="count">{{ counts.HIGH }}</div>
        <div class="label">High</div>
      </div>
      <div class="card medium">
        <div class="count">{{ counts.MEDIUM }}</div>
        <div class="label">Medium</div>
      </div>
      <div class="card low">
        <div class="count">{{ counts.LOW }}</div>
        <div class="label">Low</div>
      </div>
      <div class="card info">
        <div class="count">{{ counts.INFO }}</div>
        <div class="label">Info</div>
      </div>
      <div class="card">
        <div class="count">{{ total }}</div>
        <div class="label">Total</div>
      </div>
    </div>

    {% if summary %}
    <div class="section">
      <h2>AI Summary</h2>
      <p class="summary">{{ summary }}</p>
    </div>
    {% endif %}

    <!-- Issue table -->
    <div class="section">
      <h2>Issues ({{ total }})</h2>
      {% if issues %}
      <table>
        <thead>
          <tr>
            <th>#</th>
            <th>Severity</th>
            <th>Category</th>
            <th>Source</th>
            <th>Location</th>
            <th>Message & Suggestion</th>
          </tr>
        </thead>
        <tbody>
          {% for issue in issues %}
          <tr>
            <td>{{ loop.index }}</td>
            <td><span class="badge badge-{{ issue.severity }}">{{ issue.severity }}</span></td>
            <td>{{ issue.category or "—" }}</td>
            <td>{{ issue.source }}</td>
            <td class="location">
              {% if issue.file_path %}{{ issue.file_path }}{% endif %}
              {% if issue.line_start %}:{{ issue.line_start }}{% endif %}
            </td>
            <td>
              {{ issue.message }}
              {% if issue.suggestion %}
              <div class="suggestion">{{ issue.suggestion }}</div>
              {% endif %}
            </td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
      {% else %}
      <p style="color: #20c997; text-align: center; padding: 24px;">
        ✅ No issues found!
      </p>
      {% endif %}
    </div>

    <footer>
      🛡️ CodeGuardian AI &mdash; Every line of code, in every language, held to the highest standard.
    </footer>
  </div>
</body>
</html>"""
)


def generate_html_report(
    review_id: str,
    issues: list[AnalyzerIssue],
    summary: str = "",
    target: str | None = None,
    mode: str = "FULL",
) -> str:
    counts = Counter(i.severity for i in issues)
    return _HTML_TEMPLATE.render(
        review_id=review_id,
        issues=issues,
        summary=summary,
        target=target,
        mode=mode,
        counts={
            "CRITICAL": counts.get("CRITICAL", 0),
            "HIGH": counts.get("HIGH", 0),
            "MEDIUM": counts.get("MEDIUM", 0),
            "LOW": counts.get("LOW", 0),
            "INFO": counts.get("INFO", 0),
        },
        total=len(issues),
        generated_at=datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
    )
