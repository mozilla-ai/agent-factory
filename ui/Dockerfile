# Stage 0: Base image with dependencies
FROM node:alpine AS deps

RUN corepack enable

WORKDIR /agent-factory-ui

COPY package.json pnpm-lock.yaml ./
# prefetfch and install dependencies
RUN pnpm fetch

# Stage 1: Build the app
FROM node:lts-alpine AS builder

RUN corepack enable

WORKDIR /agent-factory-ui

COPY package.json pnpm-lock.yaml ./
# copy the prefetched pnpm store from the deps stage
COPY --from=deps /root/.local/share/pnpm/store /root/.local/share/pnpm/store

# use the prefetched pnpm store to install dependencies
RUN pnpm install --offline --frozen-lockfile

COPY . .
RUN pnpm build

# Stage 2: Production image
FROM nginx:alpine AS runner

# Remove default nginx site
RUN rm -rf /usr/share/nginx/html/*

# Copy built assets
COPY --from=builder /agent-factory-ui/dist/ /usr/share/nginx/html/

# Optional: custom nginx config
# COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
