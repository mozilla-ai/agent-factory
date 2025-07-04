FROM python:3.13.5-slim

ENV FRAMEWORK=openai
ENV MODEL=o3
ENV HOST=0.0.0.0
ENV PORT=8080
ENV LOG_LEVEL=info

WORKDIR /app

RUN pip install uv

COPY . /app

EXPOSE 8080

CMD ["sh", "-c", "uv run . --framework ${FRAMEWORK} --model ${MODEL} --host ${HOST} --port ${PORT} --log-level ${LOG_LEVEL}"]
