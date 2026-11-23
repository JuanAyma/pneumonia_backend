FROM python:3.11-slim
WORKDIR /app
COPY image_ingestion/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY image_ingestion/ .
COPY shared ./shared
EXPOSE 8001
CMD ["python", "main.py"]
