FROM python:3.10-slim

# Install system dependencies: FFmpeg for media encoding, curl and unzip to acquire Deno
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Install Deno securely to decode modern JavaScript streaming rules
RUN curl -fsSL https://deno.land/x/install/install.sh | sh
ENV DENO_INSTALL="/root/.deno"
ENV PATH="$DENO_INSTALL/bin:$PATH"

WORKDIR /app

COPY requirements.txt .
# Explicitly force pip to pull the absolute newest builds to patch breaking platform edits
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt --upgrade

COPY main.py .
COPY index.html .

EXPOSE 8000
CMD ["uvicorn", "main.py:app", "--host", "0.0.0.0", "--port", "8000"]
