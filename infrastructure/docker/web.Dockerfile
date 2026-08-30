FROM node:22-alpine

WORKDIR /workspace

RUN corepack enable

COPY package.json pnpm-workspace.yaml pnpm-lock.yaml* ./
COPY apps/web/package.json apps/web/package.json
COPY packages packages
RUN pnpm install --frozen-lockfile

COPY apps/web apps/web

EXPOSE 3000