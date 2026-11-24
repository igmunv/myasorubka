FROM python:3.11-slim

WORKDIR /app

COPY battle_manager/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY battle_manager/ .
COPY shared/ ./shared/

CMD ["python", "main.py"]
