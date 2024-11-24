FROM python:3.11-slim

# Disable Python bytecode generation and enable unbuffered output for logging
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory inside the container
WORKDIR /app

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the Flask default port (or a custom one if specified in your app)
EXPOSE 8080

# Command to run the application
CMD ["python", "app.py"]
