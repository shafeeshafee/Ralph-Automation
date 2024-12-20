FROM python:3.9-slim

ARG AGENT_NAME

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Install AWS CLI using pip
RUN pip install --upgrade pip \
    && pip install --no-cache-dir awscli

WORKDIR /app

# Copy requirements first for better caching
COPY shared/requirements.txt ./requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir \
    -r requirements.txt \
    prometheus_client requests boto3 langchain openai fastapi \
    && pip install pipdeptree \
    && pipdeptree

# Copy the shared code
COPY shared/ ./shared/

# Copy the specific agent code based on AGENT_NAME
COPY agent/${AGENT_NAME}/main.py ./main.py

# Ensure scripts are executable for analytics agents
RUN if [ "$AGENT_NAME" = "analytics" ]; then \
    mkdir -p ./scripts && \
    touch ./scripts/analyze_findings.sh && \
    chmod +x ./scripts/analyze_findings.sh; \
    fi

CMD ["python", "./main.py"]