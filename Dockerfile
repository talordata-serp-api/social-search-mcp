# Use an official lightweight Python image
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Copy the python package files
COPY pyproject.toml README.md ./
COPY src/ ./src/

# Install the package globally
RUN pip install --no-cache-dir .

# Run the server directly.
# Using 'python -m' or the console script 'social-search-mcp' over STDIO
ENTRYPOINT ["social-search-mcp"]
