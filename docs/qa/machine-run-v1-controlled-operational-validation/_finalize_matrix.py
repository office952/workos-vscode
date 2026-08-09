import json
from pathlib import Path

root = Path(__file__).resolve().parent
p = root / "scenario_matrix.json"
d = json.loads(p.read_text(encoding="utf-8"))
rows = [r for r in d["matrix"] if r["#"] not in (17, 18)]
rows.append(
    {
        "#": 17,
        "Scenario": "LIGHT_DARK_FULL_PAGE",
        "Evidence type": "BROWSER_RUNTIME_EVIDENCE",
        "Result": "SUPPORTED",
        "Limitation": "Detail lifecycle states cross-referenced from prior isolated shop-floor/closure screenshots; this GO captured QA empty list light/dark",
        "Candidate domain": "NONE",
        "Technical severity": "S0",
        "Operational frequency": "UNKNOWN",
        "notes": "QA :3000 light/dark list+create; no deferred/PAUSE",
    }
)
rows.append(
    {
        "#": 18,
        "Scenario": "REFRESH_RELOAD_DURABILITY",
        "Evidence type": "BROWSER_RUNTIME_EVIDENCE",
        "Result": "SUPPORTED",
        "Limitation": "NONE",
        "Candidate domain": "NONE",
        "Technical severity": "S0",
        "Operational frequency": "UNKNOWN",
        "notes": "reload reconstructs list from backend on QA FE",
    }
)
rows.sort(key=lambda r: r["#"])
d["matrix"] = rows
browser_path = root / "browser_capture_report.json"
if browser_path.exists():
    d["browser"] = json.loads(browser_path.read_text(encoding="utf-8"))
d["hardening_fix_candidate"] = {
    "id": "TERMINAL_MEMBERSHIP_REELIGIBILITY",
    "severity": "S3",
    "summary": (
        "find_active_membership / _active_membership_keys treat participant ACTIVE "
        "without joining MachineRun terminal status; RELEASE/CANCEL do not set "
        "participants REMOVED"
    ),
    "symptoms": [
        "CREATE after RELEASE/CANCEL → task_already_in_active_machine_run",
        "candidate discovery omits tasks still ACTIVE on CANCELLED/RELEASED runs",
        "by-task lookup correctly returns none (inconsistency)",
    ],
    "bounded_fix_scope": (
        "Filter active membership by non-terminal MachineRun status "
        "(and/or set participants REMOVED on RELEASE/CANCEL) in eligibility + "
        "create guard + candidate keys; add regression tests for re-CREATE and "
        "candidate reappear after RELEASE/CANCEL"
    ),
    "do_not_fix_in_this_go": True,
}
p.write_text(json.dumps(d, indent=2), encoding="utf-8")
for r in rows:
    print(f"{r['#']:02d} {r['Result']:28s} {r['Scenario']}")
