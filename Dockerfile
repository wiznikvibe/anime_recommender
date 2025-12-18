## Parent Image
FROM python:3.13.5-slim

## Essential Enviroment Variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*


RUN pip install --no-cache-dir uv

COPY . .

RUN uv pip install --no-cache-dir -e .

EXPOSE 8501


CMD ["streamlit", "run", "app/app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]