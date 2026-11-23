from shared.enums import RiskLevel

URGENCY = {
    RiskLevel.LOW: 72,
    RiskLevel.MODERATE: 24,
    RiskLevel.HIGH: 4,
    RiskLevel.CRITICAL: 1,
}

RISK_ORDER = [RiskLevel.LOW, RiskLevel.MODERATE, RiskLevel.HIGH, RiskLevel.CRITICAL]

def _actions_for(risk: RiskLevel, has_pathology: bool) -> list:
    if not has_pathology:
        return ["Seguimiento en 6 meses", "Mantener hábitos saludables"]
    mapping = {
        RiskLevel.MODERATE: ["Consulta médica en 48h", "Reposo relativo"],
        RiskLevel.HIGH: ["Consulta médica urgente en 4h", "Evaluar hospitalización", "Iniciar antibioticoterapia empírica"],
        RiskLevel.CRITICAL: ["Derivación de emergencia", "UCI si SpO2 < 90%", "Oxigenoterapia inmediata"],
    }
    return mapping.get(risk, ["Consulta médica programada"])

def correlate(diagnosis_id, specialization_id, diagnostic, symptom_analysis):
    has_pathology = diagnostic.get("has_pathology", False)
    image_risk = diagnostic.get("risk_level", "LOW")
    symptom_risk = symptom_analysis.get("adjusted_risk", "LOW")
    image_conf = diagnostic.get("prediction", {}).get("confidence", 0.0)
    clinical_score = symptom_analysis.get("clinical_score", 0.0)

    img_idx = RISK_ORDER.index(RiskLevel(image_risk))
    sym_idx = RISK_ORDER.index(RiskLevel(symptom_risk))
    final_idx = max(img_idx, sym_idx)
    final_risk = RISK_ORDER[final_idx]

    # Correlation score: how much image and symptoms agree
    max_idx = len(RISK_ORDER) - 1
    diff = abs(img_idx - sym_idx)
    correlation_score = round(1.0 - (diff / max_idx), 2)

    findings = []
    if has_pathology:
        findings.append(dict(
            code="J18.9",
            description="Neumonía, no especificada",
            confidence=round(image_conf, 4),
            source="IMAGE",
        ))
    if clinical_score >= 40:
        findings.append(dict(
            code="R06.0",
            description="Disnea",
            confidence=round(clinical_score / 100.0, 4),
            source="SYMPTOMS",
        ))

    return dict(
        diagnosis_id=diagnosis_id,
        findings=findings,
        final_risk=final_risk,
        urgency_hours=URGENCY[final_risk],
        recommended_actions=_actions_for(final_risk, has_pathology),
        correlation_score=correlation_score,
    )
