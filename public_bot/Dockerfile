FROM python:3.11-slim

WORKDIR /app/bot

COPY public_bot/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY public_bot/ .
COPY shared/ ./shared/

CMD ["python", "main.py"]