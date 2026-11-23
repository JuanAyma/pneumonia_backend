FROM python:3.11-slim
WORKDIR /app
COPY diagnostic/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY diagnostic/ .
COPY shared ./shared
EXPOSE 8002
CMD ["python", "main.py"]
