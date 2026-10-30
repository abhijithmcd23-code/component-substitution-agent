"""Evidence-grounded component substitution agent using synthetic data."""
import json
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent
COMPONENTS_PATH = ROOT / "data" / "components.json"
KB_PATH = ROOT / "knowledge_base"

def load_components():
    return json.loads(COMPONENTS_PATH.read_text(encoding="utf-8"))

def retrieve_rules(component_type, query, trace):
    """Simple local RAG: choose a domain document and return relevant rule lines."""
    filename = "resistor_rules.md" if component_type == "resistor" else "capacitor_rules.md"
    path = KB_PATH / filename
    lines = [line.strip("- ").strip() for line in path.read_text(encoding="utf-8").splitlines()
             if line.strip() and not line.startswith("#")]
    query_terms = set(query.lower().replace("/", " ").replace(",", " ").split())
    scored = []
    for line in lines:
        terms = set(line.lower().replace(",", " ").replace(".", " ").split())
        score = len(query_terms & terms)
        scored.append((score, line))
    scored.sort(key=lambda x: x[0], reverse=True)
    selected = [line for score, line in scored[:5] if score > 0]
    if not selected:
        selected = lines[:5]
    trace.append({
        "time": datetime.now().isoformat(timespec="seconds"),
        "step": "RAG retrieval",
        "tool": "retrieve_rules",
        "status": "success",
        "detail": f"Retrieved {len(selected)} rule(s) from {filename}",
        "evidence": selected
    })
    return selected, filename

def compare_tool(original, candidate, rules, trace):
    """Deterministic tool call: compare key specifications against engineering rules."""
    checks = []
    missing = []
    t = original["type"]

    if t == "resistor":
        specs = [
            ("resistance_ohm", "Resistance", "equal", "Nominal resistance must match."),
            ("tolerance_percent", "Tolerance (%)", "max", "Candidate tolerance must be equal to or tighter than original."),
            ("power_w", "Power rating (W)", "min", "Candidate power rating must be at least the original rating."),
            ("max_voltage_v", "Maximum voltage (V)", "min", "Candidate maximum voltage must be at least the original rating."),
        ]
    else:
        specs = [
            ("capacitance_uf", "Capacitance (µF)", "equal", "Nominal capacitance must match."),
            ("tolerance_percent", "Tolerance (%)", "max", "Candidate tolerance must be equal to or tighter than original."),
            ("voltage_rating_v", "Voltage rating (V)", "min", "Candidate voltage rating must be at least the original rating."),
        ]

    for key, label, mode, explanation in specs:
        ov, cv = original.get(key), candidate.get(key)
        if ov is None or cv is None:
            checks.append({"check": label, "original": ov, "candidate": cv, "result": "MISSING", "explanation": explanation})
            missing.append(label)
        else:
            if mode == "equal":
                passed = cv == ov
            elif mode == "max":
                passed = cv <= ov
            else:
                passed = cv >= ov
            checks.append({"check": label, "original": ov, "candidate": cv, "result": "PASS" if passed else "FAIL", "explanation": explanation})

    # A candidate's temperature range must cover the original's.
    for key, label, compare in [
        ("operating_temp_min_c", "Minimum operating temperature (°C)", lambda o,c: c <= o),
        ("operating_temp_max_c", "Maximum operating temperature (°C)", lambda o,c: c >= o),
    ]:
        ov, cv = original.get(key), candidate.get(key)
        if ov is None or cv is None:
            checks.append({"check": label, "original": ov, "candidate": cv, "result": "MISSING", "explanation": "Candidate temperature range must cover the original."})
            missing.append(label)
        else:
            checks.append({"check": label, "original": ov, "candidate": cv, "result": "PASS" if compare(ov,cv) else "FAIL", "explanation": "Candidate temperature range must cover the original."})

    ov, cv = original.get("package"), candidate.get("package")
    if ov is None or cv is None:
        checks.append({"check": "Package", "original": ov, "candidate": cv, "result": "MISSING", "explanation": "Package must match in this prototype."})
        missing.append("Package")
    else:
        checks.append({"check": "Package", "original": ov, "candidate": cv, "result": "PASS" if ov == cv else "FAIL", "explanation": "Package must match in this prototype."})

    trace.append({
        "time": datetime.now().isoformat(timespec="seconds"),
        "step": "Specification comparison",
        "tool": "compare_tool (Python)",
        "status": "success",
        "detail": f"Checked {len(checks)} compatibility conditions",
        "evidence": checks
    })
    return checks, missing

def investigate(original_id, candidate_id, feedback=None):
    """Bounded plan-act-observe loop with one retrieval retry if critical evidence is missing."""
    components = {c["part_number"]: c for c in load_components()}
    trace = []
    original, candidate = components[original_id], components[candidate_id]
    if original["type"] != candidate["type"]:
        trace.append({"time": datetime.now().isoformat(timespec="seconds"), "step": "Input validation", "tool": "type_guard", "status": "blocked", "detail": "Component types differ; comparison stopped.", "evidence": []})
        return {"verdict": "NOT COMPATIBLE", "summary": "The original and candidate are different component types.", "checks": [], "rules": [], "trace": trace, "feedback": feedback or ""}

    trace.append({"time": datetime.now().isoformat(timespec="seconds"), "step": "Plan", "tool": "planner", "status": "success", "detail": "1) Retrieve domain rules  2) Compare specifications  3) Check missing evidence  4) Decide or retry once.", "evidence": ["Loop limit: 2 comparison passes"]})
    query = f"{original['type']} substitution specifications voltage tolerance package temperature power capacitance"
    rules, source = retrieve_rules(original["type"], query, trace)
    checks, missing = compare_tool(original, candidate, rules, trace)

    if missing:
        trace.append({"time": datetime.now().isoformat(timespec="seconds"), "step": "Reflection / feedback loop", "tool": "evidence_gap_detector", "status": "retry", "detail": "Critical specification missing; agent is attempting one targeted evidence retrieval.", "evidence": missing})
        # Retry retrieval for missing evidence; the local dataset is the only evidence source.
        retry_rules, retry_source = retrieve_rules(original["type"], "missing critical specification " + " ".join(missing), trace)
        if retry_source == source:
            trace.append({"time": datetime.now().isoformat(timespec="seconds"), "step": "Retry observation", "tool": "evidence_gap_detector", "status": "inconclusive", "detail": "The local knowledge base does not contain the missing candidate datasheet value.", "evidence": missing})
    else:
        retry_rules = []

    results = [c["result"] for c in checks]
    if "FAIL" in results:
        verdict = "NOT COMPATIBLE"
        summary = "One or more compatibility checks failed. Do not substitute this candidate without engineering review."
    elif "MISSING" in results:
        verdict = "INCONCLUSIVE"
        summary = "Critical evidence is missing. The agent abstains instead of guessing; obtain a complete datasheet and review manually."
    else:
        verdict = "POTENTIALLY COMPATIBLE"
        summary = "All implemented prototype checks passed. This is not final engineering approval; verify the complete datasheet and circuit-specific requirements."
    if feedback:
        trace.append({"time": datetime.now().isoformat(timespec="seconds"), "step": "Human feedback", "tool": "feedback_handler", "status": "recorded", "detail": f"Reviewer feedback recorded: {feedback}", "evidence": ["Feedback is logged for this run; it does not override failed safety checks."]})
        if "missing" in feedback.lower() or "incomplete" in feedback.lower():
            summary += " Reviewer feedback flags incomplete evidence; manual review remains required."
    trace.append({"time": datetime.now().isoformat(timespec="seconds"), "step": "Final decision", "tool": "decision_policy", "status": "success", "detail": verdict, "evidence": [summary]})
    return {"verdict": verdict, "summary": summary, "checks": checks, "rules": rules + retry_rules, "trace": trace, "feedback": feedback or "", "original": original, "candidate": candidate}

def evaluate_examples():
    """Small fixed golden set; metrics are computed from actual agent outputs."""
    cases = [
        ("RES-A-1000", "RES-B-1000", "POTENTIALLY COMPATIBLE"),
        ("RES-A-1000", "RES-C-1000", "NOT COMPATIBLE"),
        ("RES-A-1000", "RES-D-1000", "INCONCLUSIVE"),
        ("CAP-A-10U", "CAP-B-10U", "POTENTIALLY COMPATIBLE"),
    ]
    rows = []
    for original, candidate, expected in cases:
        actual = investigate(original, candidate)["verdict"]
        rows.append({"original": original, "candidate": candidate, "expected": expected, "actual": actual, "correct": expected == actual})
    accuracy = sum(r["correct"] for r in rows) / len(rows)
    return rows, accuracy
