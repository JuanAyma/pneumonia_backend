import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from fastapi import FastAPI, HTTPException
from models import CorrelationRequest, CorrelationResponse
from service import correlate

app = FastAPI(title="Correlation Agent", version="1.0.0")

@app.get("/health")
def health():
    return {"status": "ok", "agent": "correlation", "port": 8004}

@app.post("/correlate", response_model=CorrelationResponse)
def correlate_route(req: CorrelationRequest):
    try:
        result = correlate(
            req.diagnosis_id,
            req.specialization_id,
            req.diagnostic if isinstance(req.diagnostic, dict) else req.diagnostic.dict(),
            req.symptom_analysis if isinstance(req.symptom_analysis, dict) else req.symptom_analysis.dict(),
        )
        return CorrelationResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8004)))
