FROM python:3.11-slim

# System dependencies for video rendering & audio
RUN apt-get update && apt-get install -y \
    ffmpeg \
    imagemagick \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Fix ImageMagick security policy for MoviePy text rendering
RUN sed -i 's/none/read,write/g' /etc/ImageMagick-6/policy.xml || true

# Set up user for Hugging Face Spaces (UID 1000)
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PORT=7860

WORKDIR $HOME/app

# Install Python packages
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY --chown=user . .

# Ensure outputs and data directories exist with write permissions
RUN mkdir -p outputs data

EXPOSE 7860

CMD ["python", "-m", "backend.server"]