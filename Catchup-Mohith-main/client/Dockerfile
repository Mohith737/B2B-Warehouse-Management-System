# /home/mohith/Catchup-Mohith/client/Dockerfile
FROM node:20-alpine

WORKDIR /app

COPY package.json pnpm-lock.yaml ./
RUN corepack enable && pnpm install --frozen-lockfile

COPY . .

EXPOSE 5173
CMD ["sh", "-lc", "corepack enable && pnpm install --frozen-lockfile && pnpm dev --host 0.0.0.0 --port 5173"]
