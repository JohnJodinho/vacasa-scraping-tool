# Base image with Python
FROM python:3.11

# Set non-interactive mode for apt-get
ARG DEBIAN_FRONTEND=noninteractive

# Install dependencies required for Playwright and Xvfb
RUN apt-get update -q && \
    apt-get install -y -qq --no-install-recommends \
        xvfb \
        libxcomposite1 \
        libxdamage1 \
        libatk1.0-0 \
        libasound2 \
        libdbus-1-3 \
        libnspr4 \
        libgbm1 \
        libatk-bridge2.0-0 \
        libcups2 \
        libxkbcommon0 \
        libatspi2.0-0 \
        libnss3 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Install Python dependencies and Playwright Chromium
RUN pip install --no-cache-dir -r requirements.txt && \
    playwright install chromium

# Copy application files into the container
COPY . .

# Expose the default Flask port
EXPOSE 8080

# Set the display for headless mode
ENV DISPLAY=:99

# Command to start the app
CMD Xvfb :99 -screen 0 1024x768x16 & python app.py
