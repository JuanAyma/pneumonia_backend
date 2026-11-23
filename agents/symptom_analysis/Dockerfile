FROM python:3.11-slim
WORKDIR /app
COPY symptom_analysis/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY symptom_analysis/ .
COPY shared ./shared
EXPOSE 8003
CMD ["python", "main.py"]
