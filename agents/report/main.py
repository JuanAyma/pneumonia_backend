import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from fastapi import FastAPI, HTTPException
from models import ReportRequest, ReportResponse
from service import generate

app = FastAPI(title="Report Agent", version="1.0.0")

@app.get("/health")
def health():
    return {"status": "ok", "agent": "report", "port": 8005}

@app.post("/report", response_model=ReportResponse)
def report_route(req: ReportRequest):
    try:
        result = generate(
            req.diagnosis_id,
            req.patient_id,
            req.doctor_id,
            req.specialization_id,
            req.diagnostic,
            req.symptom_analysis,
            req.correlation,
        )
        return ReportResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8005)))
