FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "idp.test", "--port", "443", "--ssl-keyfile", "idp.test+1-key.pem", " --ssl-certfile", "idp.test+1.pem", "--reload"]