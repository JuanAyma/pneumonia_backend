import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from fastapi import FastAPI, HTTPException
from models import SymptomAnalysisRequest, SymptomAnalysisResponse
from service import analyze

app = FastAPI(title="Symptom Analysis Agent", version="1.0.0")

@app.get("/health")
def health():
    return {"status": "ok", "agent": "symptom_analysis", "port": 8003}

@app.post("/analyze", response_model=SymptomAnalysisResponse)
def analyze_route(req: SymptomAnalysisRequest):
    try:
        result = analyze(
            req.diagnosis_id,
            req.specialization_id,
            req.symptoms,
            req.has_pathology,
            req.risk_level,
        )
        return SymptomAnalysisResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8003)))
