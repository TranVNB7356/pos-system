FROM python:3.11-slim

WORKDIR /app

# Copy requirements và cài Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ code
COPY . .

# Tạo thư mục cho database (nếu cần)
RUN mkdir -p /data

# Expose port
EXPOSE 10000

# Chạy ứng dụng với gunicorn
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:10000"]
