FROM python:3.11-slim
WORKDIR /app
COPY report/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY report/ .
COPY shared ./shared
EXPOSE 8005
CMD ["python", "main.py"]
