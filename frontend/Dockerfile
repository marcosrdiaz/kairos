# Mínimo (T0-01): construye la app de Vite y la sirve con nginx.
# Mientras no exista frontend/package.json (T0-07), sirve una página provisional.
# nginx reenvía /api al backend (incluye SSE de /ask y WebSocket de /voice/stt).

FROM node:22-alpine AS build
WORKDIR /src
COPY . .
RUN if [ -f package.json ]; then \
        rm -rf node_modules && \
        if [ -f package-lock.json ]; then npm ci; else npm install; fi && \
        npm run build; \
    else \
        mkdir -p dist && \
        printf '%s\n' '<!doctype html><html lang="es"><meta charset="utf-8">' \
            '<title>KAIROS</title><p>KAIROS: frontend pendiente (T0-07).</p></html>' \
            > dist/index.html; \
    fi

FROM nginx:1.27-alpine
RUN printf '%s\n' \
    'server {' \
    '  listen 80;' \
    '  root /usr/share/nginx/html;' \
    '  location /api/ {' \
    '    proxy_pass http://backend:8000;' \
    '    proxy_http_version 1.1;' \
    '    proxy_set_header Host $host;' \
    '    proxy_set_header Upgrade $http_upgrade;' \
    '    proxy_set_header Connection $http_connection;' \
    '    proxy_buffering off;' \
    '    proxy_read_timeout 3600s;' \
    '  }' \
    '  location / {' \
    '    try_files $uri $uri/ /index.html;' \
    '  }' \
    '}' > /etc/nginx/conf.d/default.conf
COPY --from=build /src/dist /usr/share/nginx/html
EXPOSE 80
