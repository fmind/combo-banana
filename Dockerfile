# https://docs.astral.sh/uv/guides/integration/docker/
# https://docs.docker.com/engine/reference/builder/
# https://github.com/astral-sh/uv-docker-example

FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS build
RUN useradd -ms /bin/bash runner
WORKDIR /home/runner
USER runner
COPY requirements.txt .
RUN uv venv && uv pip install -r requirements.txt --no-cache

FROM build AS final
ENV GOOGLE_CLOUD_LOCATION=global
ENV GOOGLE_CLOUD_PROJECT=NOT_SET
ENV GOOGLE_GENAI_USE_VERTEXAI=True
ENV GRADIO_SERVER_NAME=0.0.0.0
ENV GRADIO_SERVER_PORT=8080
ENV IMAGE_MODEL=gemini-2.5-flash-image-preview
ENV LANGUAGE_MODEL=gemini-2.5-flash
ENV LOGGING_LEVEL=INFO
ENV PYTHONUNBUFFERED=1
WORKDIR /home/runner
USER runner
COPY --from=build /home/runner/.venv ./.venv
COPY assets ./assets
COPY app.py .
CMD [".venv/bin/python", "app.py"]
