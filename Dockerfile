FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy essential shared libraries and message contracts
COPY shared/ ./shared/

# Copy agent source code
COPY agents/ ./agents/

# Set PYTHONPATH to include the /app directory for shared imports
ENV PYTHONPATH=/app

EXPOSE 8080 9090

# Command will be overridden by docker-compose
CMD ["python", "agents/observer/src/agent.py"]
