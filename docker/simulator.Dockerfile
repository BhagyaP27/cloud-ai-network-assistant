FROM python:3.12-slim

# Prevent Python from writing .pyc files and enable unbuffered logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies first (better layer caching)
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy simulator source + configs
COPY simulator /app/simulator
COPY configs /app/configs
COPY pytest.ini /app/pytest.ini

# Default command: run the simulator using the dev config
CMD ["python", "-m", "simulator.main", "--config", "configs/simulator.dev.yaml"]
