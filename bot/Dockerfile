FROM harbor.pg.innopolis.university/docker-hub-cache/python:3.12-slim

WORKDIR /app

# Copy all bot files
COPY bot/ ./bot/
COPY pyproject.toml ./

# Install dependencies from cached packages
RUN apt-get update && apt-get install -y curl && \
    curl -LsSf https://astral.sh/uv/install.sh | sh && \
    export PATH="$HOME/.local/bin:$PATH" && \
    uv sync --locked --no-install-project 2>/dev/null || \
    pip install httpx python-telegram-bot

# Set environment
ENV PYTHONPATH=/app
ENV PATH="/root/.local/bin:$PATH"

# Run the bot
CMD ["python", "bot/bot.py"]
