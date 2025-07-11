FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Cloudtype에서는 CMD를 동적으로 지정할 수 있으므로 기본값은 FastAPI 서버로 설정
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"] 