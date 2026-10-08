FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 AGROINTEL_ROOT=/app
WORKDIR /app
COPY requirements-lock.txt pyproject.toml ./
RUN pip install --no-cache-dir -r requirements-lock.txt
COPY src ./src
COPY configs ./configs
COPY artifacts ./artifacts
COPY reports ./reports
COPY examples ./examples
RUN pip install --no-cache-dir --no-deps . && useradd --create-home agrointel
USER agrointel
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=4)" || exit 1
CMD ["uvicorn", "agrointel.web:app", "--host", "0.0.0.0", "--port", "8000"]
