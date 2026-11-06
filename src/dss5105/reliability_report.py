"""Read-only HTML projection of an offline reliability report; no scoring or live calls."""

import html
import json
from collections import Counter

OUTCOMES = ("FAIL", "NOT_SCORABLE", "UNRESOLVED_POLICY", "PASS", "NOT_APPLICABLE")


def _text(value):
    return html.escape(str(value), quote=True)


def _json(value):
    return _text(json.dumps(value, sort_keys=True, ensure_ascii=True, allow_nan=False, indent=2))


def _options(values):
    return "".join(f'<option value="{_text(value)}">{_text(value)}</option>' for value in sorted(set(values)))


def render_html_report(report, manifest):
    """Render existing outcomes faithfully, without changing the report or inventing a total score."""
    cases, summary = report["cases"], report["summary"]
    assertions = [(case, check) for case in cases for check in case["checks"]]
    counts = Counter(check["outcome"] for _, check in assertions)
    badges = "".join(
        f'<span class="badge {outcome}">{outcome} <strong>{counts[outcome]}</strong></span>' for outcome in OUTCOMES
    )
    case_rows = []
    for case in cases:
        compatibility = case["compatibility"]
        issues = "; ".join(compatibility["issues"]) or "None"
        execution = case["execution"]["outcome"] or "not attempted / unknown"
        case_rows.append(
            f"<tr><td>{_text(case['case_id'])}</td><td>{_text(execution)}</td>"
            f"<td>{'Yes' if compatibility['compatible'] else 'No'}</td>"
            f"<td>{_text(case['adjudication_state'])}</td><td>{_text(issues)}</td></tr>"
        )
    metric_rows = []
    for metric in summary["metrics"]:
        if not metric["coverage"]["declared_checks"]:
            continue
        coverage = metric["coverage"]
        value = "null (no evaluable assertions)" if metric["value"] is None else f"{metric['value']:.4f}"
        rate_type = (
            "violation rate (lower is better)"
            if metric["metric"].endswith("violation_rate")
            or metric["metric"] == "duplicate_standard_clarification_rate"
            else "pass / recall rate"
        )
        metric_rows.append(
            f"<tr><td>{_text(metric['metric'])}<br><small>{rate_type}</small></td>"
            f"<td>{_text(metric['annotation_basis'])}</td>"
            f"<td>{metric['numerator']} / {metric['denominator']}<br><small>{value}</small></td>"
            f"<td>{coverage['evaluable_assertions']} / {coverage['eligible_assertions']}</td>"
            f"<td>{metric['outcome_counts']['NOT_SCORABLE']}</td>"
            f"<td>{metric['outcome_counts']['UNRESOLVED_POLICY']}</td></tr>"
        )
    check_rows = []
    for case, check in sorted(
        assertions, key=lambda pair: (OUTCOMES.index(pair[1]["outcome"]), pair[0]["case_id"], pair[1]["id"])
    ):
        outcome = check["outcome"]
        observed = (
            "<em>Missing evidence (not JSON null)</em>"
            if check["observed_missing"]
            else (f"<pre>{_json(check['observed'])}</pre>")
        )
        paths = "<br>".join(_text(path) for path in check["evidence_paths"]) or "No path declared"
        check_rows.append(
            f'<tr class="assertion" data-case="{_text(case["case_id"])}" '
            f'data-outcome="{outcome}" data-basis="{_text(check["annotation_basis"])}">'
            f'<td>{_text(case["case_id"])}</td><td><span class="badge {outcome}">{outcome}</span></td>'
            f"<td><strong>{_text(check['metric'])}</strong><br>{_text(check['annotation_basis'])}"
            f"<details><summary>{_text(check['id'])}</summary>"
            f"<p>Reason: <code>{_text(check['reason_code'])}</code></p>"
            f"<h4>Expected</h4><pre>{_json(check['expected'])}</pre>"
            f"<h4>Observed</h4>{observed}<h4>Evidence paths in saved artifact</h4>"
            f"<code>{paths}</code></details></td></tr>"
        )
    provenance = {
        "source_type": summary["source_type"],
        "scorer_version": manifest.get("scorer_version"),
        "scorer_content_hash": manifest.get("scorer_content_hash"),
        "benchmark_content_hash": manifest.get("benchmark_content_hash"),
        "input_artifact_hash": manifest.get("input_artifact_hash"),
        "report_renderer_content_hash": manifest.get("report_renderer_content_hash"),
        "run_provenance": manifest.get("run_provenance", {}),
    }
    return (
        HEADER
        + '<main><p class="eyebrow">STITCHFLOW / OFFLINE EVALUATOR</p><h1>Evidence before scores</h1>'
        + "<p>Review a saved run: compatibility, individual assertions, and scoring coverage.</p>"
        + f'<p class="notice">Source: <strong>{_text(summary["source_type"])}</strong>. '
        + "Provisional labels are not independent human gold. Synthetic fixtures are not model accuracy.</p>"
        + '<section class="stats">'
        + f"<div><strong>{summary['planned']}</strong>Planned cases</div>"
        + f"<div><strong>{summary['attempted']}</strong>Attempted cases</div>"
        + f"<div><strong>{report['compatibility']['compatible_attempted_cases']}</strong>"
        + "Compatible attempted cases</div>"
        + "</section><h2>1. Check the context</h2><p>Incompatible evidence must not become a semantic pass.</p>"
        + '<div class="table-wrap"><table><thead><tr><th>Case</th><th>Execution</th><th>Compatible</th>'
        + "<th>Review state</th><th>Compatibility issues</th></tr></thead><tbody>"
        + "".join(case_rows)
        + "</tbody></table></div><h2>2. Inspect assertions</h2>"
        + "<p>These are assertion counts, including overlapping checks. They are not independent samples "
        + 'or an overall accuracy score.</p><p class="badges">'
        + badges
        + '</p><div class="filters"><label>Case<select id="case"><option value="">All cases</option>'
        + _options(case["case_id"] for case in cases)
        + '</select></label><label>Outcome<select id="outcome"><option value="attention">FAIL + NOT_SCORABLE</option>'
        + '<option value="">All outcomes</option>'
        + _options(OUTCOMES)
        + '</select></label><label>Basis<select id="basis"><option value="">All bases</option>'
        + _options(check["annotation_basis"] for _, check in assertions)
        + '</select></label><label>Search<input id="search" type="search" '
        + 'placeholder="cost, reason, evidence..."></label>'
        + '<button id="reset" type="button">Show all</button></div><p id="shown" aria-live="polite"></p>'
        + '<div class="table-wrap"><table><thead><tr><th>Case</th><th>Outcome</th><th>Assertion and evidence</th>'
        + "</tr></thead><tbody>"
        + "".join(check_rows)
        + "</tbody></table></div><h2>3. Read each denominator</h2>"
        + "<p>Rate denominator = PASS + FAIL. Coverage = (PASS + FAIL) / "
        + "(PASS + FAIL + NOT_SCORABLE). UNRESOLVED_POLICY and NOT_APPLICABLE are excluded. "
        + "A zero denominator gives null. Do not average these metrics into one score.</p>"
        + '<div class="table-wrap"><table><thead><tr><th>Metric</th><th>Basis</th><th>Numerator / denominator</th>'
        + "<th>Coverage count</th><th>Not scorable</th><th>Unresolved</th></tr></thead><tbody>"
        + "".join(metric_rows)
        + "</tbody></table></div><h2>4. Trace the run</h2><pre>"
        + _json(provenance)
        + '</pre><p>Canonical files: <a href="cases.jsonl">cases.jsonl</a>, '
        + '<a href="summary.json">summary.json</a>, <a href="checks.csv">checks.csv</a>, '
        + '<a href="manifest.json">manifest.json</a>. This report cannot rescore or change a saved run.</p>'
        + "<p>Limits: no complete free-text explanation faithfulness, semantic paraphrase detection, "
        + "multi-turn performance assessment, or new model evaluation is established by this view.</p></main>"
        + SCRIPT
        + "</body></html>\n"
    )


HEADER = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline';
script-src 'unsafe-inline'; base-uri 'none'; form-action 'none'">
<title>StitchFlow Offline Evaluator</title><style>
:root{font:15px/1.6 system-ui,sans-serif;color:#182b42;background:#f5f7fb}
body{margin:0}main{max-width:1120px;margin:0 auto;padding:42px 24px 70px}
h1{font-size:38px;line-height:1.2;margin:8px 0 12px;letter-spacing:-1px}h2{margin-top:36px}
.eyebrow{font-size:12px;font-weight:750;letter-spacing:2px;color:#45617e}
.notice{border-left:4px solid #c99127;padding:12px 16px;background:#fff8e8}
.stats{display:flex;gap:14px;margin:24px 0}.stats div{background:white;border:1px solid #dae2ed;
padding:18px 24px;flex:1;border-radius:10px}.stats strong{display:block;font-size:30px;color:#1f578e}
table{width:100%;border-collapse:collapse;background:white}th,td{padding:12px 14px;text-align:left;
vertical-align:top;border-bottom:1px solid #e5eaf2}th{background:#edf2f8;font-size:12px;color:#45617e}
.table-wrap{overflow:auto;border:1px solid #dce4ef;border-radius:8px}td{font-size:13px}
.badge{display:inline-block;padding:3px 8px;border-radius:5px;font-size:11px;white-space:nowrap;
font-weight:700}.PASS{background:#e0f2e9;color:#17583c}.FAIL{background:#ffe0dd;color:#9b3025}
.NOT_SCORABLE{background:#fff0d0;color:#86580c}.UNRESOLVED_POLICY{background:#e9e2fa;color:#603c96}
.NOT_APPLICABLE{background:#e9edf3;color:#536174}.badges{display:flex;gap:10px;flex-wrap:wrap}
.filters{display:flex;gap:12px;align-items:end;flex-wrap:wrap;margin:20px 0 10px}
label{font-size:12px;font-weight:650}select,input,button{display:block;font:inherit;padding:9px;
border:1px solid #bfcede;border-radius:5px;background:white;color:#182b42}
button{cursor:pointer}small{color:#64748b}code,pre{font-family:Consolas,monospace;font-size:12px}
pre{background:#f0f4f9;padding:12px;white-space:pre-wrap;overflow-wrap:anywhere;border-radius:6px}
details{margin-top:8px}summary{cursor:pointer;overflow-wrap:anywhere}h4{margin:14px 0 3px}
td:last-child{overflow-wrap:anywhere}a{color:#215f9d}[hidden]{display:none!important}
@media(max-width:640px){.stats{flex-direction:column}main{padding:24px 14px}h1{font-size:30px}}
</style></head><body>"""

SCRIPT = """<script>
const rows = [...document.querySelectorAll('.assertion')];
const byId = id => document.getElementById(id);
function applyFilters() {
  const selectedCase = byId('case').value;
  const outcome = byId('outcome').value;
  const basis = byId('basis').value;
  const search = byId('search').value.toLowerCase();
  let visible = 0;
  for (const row of rows) {
    const match = (!selectedCase || row.dataset.case === selectedCase) &&
      (!basis || row.dataset.basis === basis) &&
      (!outcome || (outcome === 'attention' ?
        ['FAIL', 'NOT_SCORABLE'].includes(row.dataset.outcome) : row.dataset.outcome === outcome)) &&
      row.textContent.toLowerCase().includes(search);
    row.hidden = !match;
    if (match) visible++;
  }
  byId('shown').textContent = visible + ' of ' + rows.length + ' assertions shown.' +
    (visible ? ' Expand an assertion to inspect evidence.' : ' Select All outcomes to inspect other checks.');
}
for (const id of ['case', 'outcome', 'basis', 'search']) byId(id).addEventListener('input', applyFilters);
byId('reset').addEventListener('click', () => {
  for (const id of ['case', 'outcome', 'basis', 'search']) byId(id).value = '';
  applyFilters();
});
applyFilters();
</script>"""
