# Imagen para desplegar en Docker / Kubernetes / Azure App Service para contenedores.
# La plataforma debe publicarla detrás de HTTPS y pasar las variables de .env.example.
FROM node:22-alpine
WORKDIR /app
ENV NODE_ENV=production AUDIT_FILE=stdout TRUST_PROXY=true PORT=3000
COPY package.json package-lock.json ./
RUN npm ci --omit=dev
COPY server.js ./
COPY src ./src
COPY public ./public
COPY config ./config
USER node
EXPOSE 3000
HEALTHCHECK CMD wget -qO- http://127.0.0.1:3000/healthz || exit 1
CMD ["node", "server.js"]
