FROM python:3.11-slim

WORKDIR /app

# Cài đặt dependencies hệ thống cần thiết cho psycopg2
RUN apt-get update && apt-get install -y libpq-dev gcc && rm -rf /var/lib/apt/lists/*

# Copy requirements và cài Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ code
COPY . .

# Chạy ứng dụng
CMD gunicorn app:app --bind 0.0.0.0:$PORT
