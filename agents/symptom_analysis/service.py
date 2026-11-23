from shared.enums import RiskLevel

RISK_ORDER = [RiskLevel.LOW, RiskLevel.MODERATE, RiskLevel.HIGH, RiskLevel.CRITICAL]

PULMONOLOGY_RULES = [
    {"field": "fever",   "op": "gte", "threshold": 38.0, "weight": 25, "severity": "WARNING"},
    {"field": "fever",   "op": "gte", "threshold": 39.5, "weight": 15, "severity": "CRITICAL"},
    {"field": "oxygen",  "op": "lte", "threshold": 94.0, "weight": 30, "severity": "WARNING"},
    {"field": "oxygen",  "op": "lte", "threshold": 90.0, "weight": 20, "severity": "CRITICAL"},
    {"field": "cough",   "op": "eq",  "threshold": True,  "weight": 15, "severity": "WARNING"},
]

def _rules_for(specialization_id: str):
    if specialization_id == "pulmonology":
        return PULMONOLOGY_RULES
    return []

def analyze(diagnosis_id: str, specialization_id: str, symptoms: dict, has_pathology: bool, risk_level: RiskLevel):
    rules = _rules_for(specialization_id)
    score = 0.0
    alerts = []

    for rule in rules:
        val = symptoms.get(rule["field"])
        if val is None:
            continue
        triggered = False
        if rule["op"] == "gte" and float(val) >= rule["threshold"]:
            triggered = True
        elif rule["op"] == "lte" and float(val) <= rule["threshold"]:
            triggered = True
        elif rule["op"] == "eq" and val == rule["threshold"]:
            triggered = True

        if triggered:
            score += rule["weight"]
            alerts.append(dict(
                field_id=rule["field"],
                value=val,
                threshold=rule["threshold"],
                severity=rule["severity"],
            ))

    score = min(score, 100.0)

    # Escalate risk if clinical score is severe
    base_idx = RISK_ORDER.index(risk_level)
    if score >= 50 and has_pathology:
        adjusted_idx = min(base_idx + 1, len(RISK_ORDER) - 1)
    else:
        adjusted_idx = base_idx
    adjusted_risk = RISK_ORDER[adjusted_idx]

    has_critical = any(a["severity"] == "CRITICAL" for a in alerts)
    summary = (
        f"Síntomas clínicos indican riesgo {'crítico' if has_critical else 'moderado'}. "
        f"Score: {score:.0f}/100."
        if alerts else
        "Sin alertas clínicas significativas."
    )

    return dict(
        diagnosis_id=diagnosis_id,
        clinical_score=round(score, 1),
        alerts=alerts,
        adjusted_risk=adjusted_risk,
        summary=summary[:200],
    )
