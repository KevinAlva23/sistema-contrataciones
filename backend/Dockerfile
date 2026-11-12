FROM docker.io/library/python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY main.py alembic.ini ./
COPY alembic ./alembic
RUN mkdir /data
CMD ["sh", "-c", "if echo \"$DATABASE_URL\" | grep -q postgresql; then alembic upgrade head; fi; uvicorn main:app --host 0.0.0.0 --port 8000"]
