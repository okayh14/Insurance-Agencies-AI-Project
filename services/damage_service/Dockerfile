FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY shared/ ./shared/
COPY services/damage_service/ ./services/damage_service/

ENV PYTHONUNBUFFERED=1

CMD ["uvicorn", "services.damage_service.main:app", "--host", "0.0.0.0", "--port", "8000"]
