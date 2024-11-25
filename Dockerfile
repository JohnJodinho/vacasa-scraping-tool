# Use an official Python runtime as the base image
FROM python:3.11

# Suppress prompts during package installation
ARG DEBIAN_FRONTEND=noninteractive

# Install system dependencies for Playwright and Chromium
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
        libnss3

# Copy project files (including app.py and requirements.txt)
COPY . /app

# Set the working directory
WORKDIR /app

# Install Python dependencies
RUN pip3 install -r requirements.txt && \
    playwright install chromium

# Set up the virtual display for Playwright
ENV DISPLAY=:99

# Expose the port Gunicorn will listen on
EXPOSE 8080

# Run the app using Gunicorn
CMD Xvfb :99 -screen 0 1024x768x16 & gunicorn --bind 0.0.0.0:8080 app:app
