FROM python:3.11-slim
WORKDIR /app
COPY correlation/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY correlation/ .
COPY shared ./shared
EXPOSE 8004
CMD ["python", "main.py"]
