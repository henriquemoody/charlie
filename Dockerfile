# Build stage
FROM python:3.11-slim as builder

WORKDIR /build

# Install git and build dependencies (needed for hatch-vcs)
RUN apt-get update && \
    apt-get install -y --no-install-recommends git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy source code (including .git for version detection)
COPY . .

# Build wheel package
RUN pip install --no-cache-dir build && \
    python -m build --wheel && \
    ls -la dist/

# Runtime stage
FROM python:3.11-slim

WORKDIR /app

# Copy and install the wheel from builder
COPY --from=builder /build/dist/*.whl /app/
RUN pip install --no-cache-dir /app/*.whl && \
    rm -f /app/*.whl && \
    charlie --help

# Set the working directory to /workspace for user projects
WORKDIR /workspace

# Use the charlie CLI as entrypoint
ENTRYPOINT ["charlie"]

# Default to showing help
CMD ["--help"]

