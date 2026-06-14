FROM python:3.10-slim

# Install system utilities: FFmpeg for conversion + Node.js for signature decryption
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | gen_node_install_script=1 bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .
COPY index.html .

EXPOSE 8000
CMD ["uvicorn", "main.py:app", "--host", "0.0.0.0", "--port", "8000"]
