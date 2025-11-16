FROM python:3.11-slim
WORKDIR /app

# install deps
COPY ../../requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copy this service's code (depends on build context above)
COPY . .

# ensure local imports like "import models" work
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
