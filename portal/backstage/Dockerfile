# Multi-stage Dockerfile for Backstage on Cloud Run
# Based on Backstage's official Dockerfile

# Stage 1: Build
FROM node:20-bookworm-slim AS build

ENV PYTHON=/usr/bin/python3

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends python3 g++ build-essential libsqlite3-dev && \
    rm -rf /var/lib/apt/lists/*

# Copy everything
COPY . .

# Install dependencies
RUN yarn install --immutable

# Build backend (creates bundle.tar.gz and skeleton.tar.gz)
RUN yarn build:backend

# Stage 2: Production
FROM node:20-bookworm-slim

ENV PYTHON=/usr/bin/python3
ENV NODE_ENV=production
ENV NODE_OPTIONS="--no-node-snapshot"

RUN apt-get update && \
    apt-get install -y --no-install-recommends python3 g++ build-essential libsqlite3-dev && \
    rm -rf /var/lib/apt/lists/*

USER node
WORKDIR /app

# Copy yarn files
COPY --chown=node:node .yarn ./.yarn
COPY --chown=node:node .yarnrc.yml ./
COPY --chown=node:node backstage.json ./

# Copy skeleton and install production deps
COPY --from=build --chown=node:node /app/yarn.lock /app/package.json ./
COPY --from=build --chown=node:node /app/packages/backend/dist/skeleton.tar.gz ./
RUN tar xzf skeleton.tar.gz && rm skeleton.tar.gz

RUN yarn workspaces focus --all --production

# Copy catalog examples
COPY --chown=node:node examples ./examples

# Copy bundle and configs
COPY --from=build --chown=node:node /app/packages/backend/dist/bundle.tar.gz ./
COPY --chown=node:node app-config.yaml app-config.production.yaml ./
RUN tar xzf bundle.tar.gz && rm bundle.tar.gz

ENV PORT=8080
EXPOSE 8080

CMD ["node", "packages/backend", "--config", "app-config.yaml", "--config", "app-config.production.yaml"]
