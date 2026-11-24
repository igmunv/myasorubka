FROM python:3.11-slim

WORKDIR /app/bot

COPY admin_bot/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY admin_bot/ .
COPY shared/ ./shared/

CMD ["python", "main.py"]