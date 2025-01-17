# Stage 1: Build stage
FROM node:20 AS builder

COPY ui /app
WORKDIR /app
RUN yarn install
RUN PUBLIC_URL=/static npm run build

# Stage 2: Production stage
FROM python:3.12.8-slim

WORKDIR /app
COPY core/requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY --from=builder /app/build /app/ui/build
COPY app/   /app/app
COPY arrow/ /app/arrow
COPY core/  /app/core

CMD ["python3", "app/server.py"]
