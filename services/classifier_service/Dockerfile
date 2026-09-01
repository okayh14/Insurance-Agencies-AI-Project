FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY shared/ ./shared/
COPY services/classifier_service/ ./services/classifier_service/

ENV PYTHONUNBUFFERED=1

CMD ["uvicorn", "services.classifier_service.main:app", "--host", "0.0.0.0", "--port", "8000"]
