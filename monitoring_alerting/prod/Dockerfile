FROM python:3.9-slim

ARG AGENT_NAME

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Install AWS CLI
RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" \
    && unzip awscliv2.zip

WORKDIR /agent

# Copy requirements first for better caching
COPY shared/requirements.txt ./requirements.txt

# Install Python dependencies with specific order
RUN pip install --no-cache-dir pydantic==1.10.8 \
    && pip install --no-cache-dir pydantic-core==2.14.5 \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install prometheus_client requests boto3

# Copy the rest of the application
COPY shared/ ./shared/
COPY agent/${AGENT_NAME}/main.py ./main.py

# If this is the analytics agent, copy the analysis script
RUN if [ "$AGENT_NAME" = "analytics" ]; then \
    mkdir -p ./scripts && \
    touch ./scripts/analyze_findings.sh && \
    chmod +x ./scripts/analyze_findings.sh; \
    fi

CMD ["python", "./main.py"]