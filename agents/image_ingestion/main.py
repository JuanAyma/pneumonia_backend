import os
from fastapi import FastAPI, HTTPException
from models import ImageIngestionRequest, ImageIngestionResponse
from service import process_image

app = FastAPI(title="Image Ingestion Agent", version="1.0.0")

@app.get("/health")
def health():
    return {"status": "ok", "agent": "image_ingestion", "port": 8001}

@app.post("/ingest", response_model=ImageIngestionResponse)
def ingest(req: ImageIngestionRequest):
    try:
        result = process_image(req.image_base64, req.diagnosis_id)
        return ImageIngestionResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8001)))
