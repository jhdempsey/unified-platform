# Stage 1: Build
FROM node:20-bookworm-slim AS build

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    g++ \
    make \
    && rm -rf /var/lib/apt/lists/*

# Copy package files
COPY package.json yarn.lock .yarnrc.yml ./
COPY .yarn ./.yarn
COPY packages/app/package.json ./packages/app/
COPY packages/backend/package.json ./packages/backend/

# Install dependencies
RUN yarn install --immutable

# Copy source
COPY . .

# Build
RUN yarn tsc
RUN yarn build:backend

# Stage 2: Production
FROM node:20-bookworm-slim

WORKDIR /app

# Install production dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    && rm -rf /var/lib/apt/lists/*

# Copy built backend
COPY --from=build /app/packages/backend/dist ./packages/backend/dist
COPY --from=build /app/node_modules ./node_modules
COPY --from=build /app/package.json ./
COPY --from=build /app/yarn.lock ./
COPY --from=build /app/.yarnrc.yml ./
COPY --from=build /app/.yarn ./.yarn

# Copy app-config
COPY app-config.yaml app-config.production.yaml ./

# Copy catalog files
COPY examples ./examples

ENV NODE_ENV=production
ENV PORT=8080

EXPOSE 8080

# Use production config
CMD ["node", "packages/backend/dist/index.js", "--config", "app-config.yaml", "--config", "app-config.production.yaml"]
