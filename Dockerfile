FROM python:3.12-slim

WORKDIR /app

# Install Node.js for MCP servers (npx) and web dashboard
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl git && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy and install Python package
COPY pyproject.toml README.md LICENSE ./
COPY lifeclaw/ lifeclaw/
RUN pip install --no-cache-dir -e .

# Build web dashboard
COPY web/ web/
RUN cd web && npm install --silent && npm run build 2>/dev/null || true

# Default config dir
RUN mkdir -p /root/.lifeclaw

EXPOSE 3119 3120

ENTRYPOINT ["lifeclaw"]
CMD ["chat"]
