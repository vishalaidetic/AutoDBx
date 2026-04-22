FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including Databricks CLI requirements
RUN apt-get update && apt-get install -y \
    curl \
    git \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Install Databricks CLI
RUN curl -fsSL https://raw.githubusercontent.com/databricks/setup-cli/main/install.sh | sh

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source code
COPY . .

EXPOSE 8000

# Set dynamic root for AutoDBx
ENV AUTO_DBX_ROOT=/migration_projects

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
