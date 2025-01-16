
# Python version
FROM python:3.10

# 與效能有關的設定
ENV PIP_NO_CACHE_DIR off
ENV PIP_DISABLE_PIP_VERSION_CHECK on
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

# Set the working directory in docker
WORKDIR /app

# Copy the dependencies file to the working directory
COPY requirements.txt .

# Install any dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the content of the local src directory to the working directory
COPY . .

# List the contents of /app
RUN ls -l /app

# Ensure proper permissions for entrypoint script
# Fix potential permission denied errors on various environments
RUN chmod +x /app/entrypoint.sh 

# Entry point
ENTRYPOINT [ "/bin/bash", "/app/entrypoint.sh" ]
