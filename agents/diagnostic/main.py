import os
from fastapi import FastAPI, HTTPException
from models import DiagnosticRequest, DiagnosticResponse
from service import run_inference

app = FastAPI(title="Diagnostic Agent", version="1.0.0")

@app.get("/health")
def health():
    return {"status": "ok", "agent": "diagnostic", "port": 8002}

@app.post("/diagnose", response_model=DiagnosticResponse)
def diagnose(req: DiagnosticRequest):
    try:
        result = run_inference(req.normalized_path, req.diagnosis_id, req.specialization_id)
        return DiagnosticResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8002)))
