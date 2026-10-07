# Use lightweight official Python runtime
FROM python:3.11-slim

# Set timezone environment to Indian Standard Time
ENV TZ=Asia/Kolkata
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Expose HTTP health port
EXPOSE 8080

# Run the cloud scheduler daemon
CMD ["python", "-u", "cloud_scheduler.py"]
