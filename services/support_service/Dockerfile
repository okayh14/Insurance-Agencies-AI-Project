FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY shared/ ./shared/
COPY services/support_service/ ./services/support_service/

ENV PYTHONUNBUFFERED=1

CMD ["uvicorn", "services.support_service.main:app", "--host", "0.0.0.0", "--port", "8000"]
