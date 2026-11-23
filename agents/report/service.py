import json
import os
import time
from datetime import datetime, timezone

REPORT_DIR = os.environ.get("REPORT_DIR", "/tmp/pneumonia_reports")
os.makedirs(REPORT_DIR, exist_ok=True)

def generate(diagnosis_id, patient_id, doctor_id, specialization_id, diagnostic, symptom_analysis, correlation):
    t0 = time.time()

    report_data = {
        "diagnosis_id": diagnosis_id,
        "patient_id": patient_id,
        "doctor_id": doctor_id,
        "specialization_id": specialization_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "diagnostic": diagnostic if isinstance(diagnostic, dict) else diagnostic.dict(),
        "symptom_analysis": symptom_analysis if isinstance(symptom_analysis, dict) else symptom_analysis.dict(),
        "correlation": correlation if isinstance(correlation, dict) else correlation.dict(),
    }

    report_path = os.path.join(REPORT_DIR, f"{diagnosis_id}_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2, default=str)

    return dict(
        diagnosis_id=diagnosis_id,
        report_s3_key=f"reports/{diagnosis_id}/report.json",
        report_url=f"file://{report_path}",
        notification_sent=False,  # FCM/SNS not wired in MVP
        notification_channel="NONE",
        generated_at=report_data["generated_at"],
        page_count=1,
    )
