# Use official miniconda base image for reliable Python environment
FROM continuumio/miniconda3:latest

# Set working directory for application
WORKDIR /app

# Create non-root user and set up directory structure
# - Create appuser group and user
# - Create necessary directories
# - Set proper ownership
RUN groupadd -r appuser && \
    useradd -r -g appuser -s /bin/bash appuser && \
    mkdir -p /app/config /app/logs && \
    chown -R appuser:appuser /app

# Copy application files with correct ownership
COPY --chown=appuser:appuser . /app/

# Create and configure conda environment
# - Create Python 3.12 environment
# - Add activation to bashrc for interactive use
RUN conda create -n domain-sentinel python=3.12 -y && \
    echo "conda activate domain-sentinel" >> ~/.bashrc

# Configure shell for conda environment activation
SHELL ["/bin/bash", "--login", "-c"]

# Install dependencies
# - Activate conda environment
# - Install Python packages from requirements.txt
RUN conda activate domain-sentinel && \
    pip install -r requirements.txt && \
    # Clean conda caches to reduce image size
    conda clean -afy && \
    # Clean pip cache
    pip cache purge

# Define persistent storage volumes
# - /app/config: Configuration files
# - /app/logs: Application logs
VOLUME ["/app/config", "/app/logs"]

# Switch to non-root user for security
USER appuser

# Configure container health monitoring
# - Check every 30 seconds
# - 10 second timeout
# - 5 second startup grace period
# - 3 retries before marking unhealthy
# - Verifies python process is running
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD ps aux | grep python | grep app.py || exit 1

# Set the entry point
# - Use conda run to ensure correct environment
# - Execute main application
ENTRYPOINT ["conda", "run", "-n", "domain-sentinel", "python", "app.py"]

# Build-time metadata
LABEL maintainer="Domain Sentinel Team" \
      version="1.0" \
      description="Domain expiration monitoring system" \
      org.opencontainers.image.source="https://github.com/YQ131026/domain-sentinel"