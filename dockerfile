# Stage 1: Build stage
FROM node:20 AS builder

COPY ui /app
WORKDIR /app
RUN yarn install
RUN PUBLIC_URL=/static npm run build

# Stage 2: Production stage
FROM python:3.12.8-slim

WORKDIR /app
COPY --from=builder /app/build /app/ui/build
COPY app/   /app/app
COPY arrow/ /app/arrow
COPY core/  /app/core

# install fonts
RUN apt-get update && apt-get install -y fontconfig
RUN mkdir -p /usr/share/fonts/custom/
COPY fonts/* /usr/share/fonts/custom/
RUN fc-cache -fv

# install python dependencies
RUN pip install -r /app/core/requirements.txt

CMD ["python3", "app/server.py"]
