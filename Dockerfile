# Use official Python image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy requirements (if you have a requirements.txt)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Expose port
EXPOSE 8000

# Set environment variables (optional)
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Run Django server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
