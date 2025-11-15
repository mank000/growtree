FROM python:3.13-slim
RUN pip install --no-cache-dir poetry
WORKDIR /app
COPY ./max_bot /app

RUN chmod +x /app/entrypoint.sh

COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root
COPY . .
ENV PYTHONUNBUFFERED=1
CMD ["/app/entrypoint.sh"]

