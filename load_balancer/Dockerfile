FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY load_balancer/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY load_balancer/ ./load_balancer/

# Expose the port the app runs on
EXPOSE 5000

# Command to run the application
CMD ["python", "-m", "load_balancer.load_balancer"]
