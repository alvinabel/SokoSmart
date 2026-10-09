FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=5001

WORKDIR /src

# shared/ is the cross-service library — both Dockerfiles copy it so images stay self-contained.
COPY shared ./shared
COPY backend ./backend

WORKDIR /src/backend
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5001
CMD ["gunicorn", "app:app", "-b", "0.0.0.0:5001", "--workers", "2", "--timeout", "60"]