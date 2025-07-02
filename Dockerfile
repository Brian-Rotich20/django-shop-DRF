FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .
ENV PATH=/root/.local/bin:$PATH
RUN python manage.py collectstatic --noinput || true
CMD ["daphne", "ecommerceApiProject.asgi:application", "-b", "0.0.0.0", "-p", "8000"]