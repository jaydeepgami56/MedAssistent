FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

# Install Node.js 20 LTS, LibreOffice, Poppler (pdftoppm), Python 3 + pip
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends \
    nodejs \
    libreoffice-impress libreoffice-writer libreoffice-calc \
    poppler-utils \
    python3 python3-pip \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install FastAPI + uvicorn (Python HTTP server for the worker API)
RUN pip3 install fastapi uvicorn --break-system-packages

# Pre-install pptxgenjs globally so each job skips the npm install step
# (per-job install still works as fallback if the global version is unavailable)
RUN npm install -g pptxgenjs

# Output directory — should be bind-mounted from the host
RUN mkdir -p /ppt_outputs

WORKDIR /app
COPY server.py .

EXPOSE 8001
CMD ["python3", "-m", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8001"]
