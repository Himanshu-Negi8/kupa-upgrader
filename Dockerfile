FROM python:3.9-slim

WORKDIR /app

# Install git
RUN apt-get update && apt-get install -y git && apt-get clean

# Copy the project files
COPY . /app/

# Install the package
RUN pip install --no-cache-dir -e .

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV OPENAI_API_KEY=""
ENV GITHUB_TOKEN=""

# Expose port for the API server
EXPOSE 8080

# Set the entrypoint
ENTRYPOINT ["kupa"]

# Default command (can be overridden)
CMD ["--help"]
