# Stage 1: Builder
FROM node:22-alpine AS builder

RUN npm install -g pnpm@9

WORKDIR /app

COPY package.json pnpm-lock.yaml ./

RUN pnpm install --frozen-lockfile || pnpm install

COPY . .

RUN pnpm run build

# Stage 2: Runner (production)
FROM node:22-alpine AS runner

RUN npm install -g pnpm@9

WORKDIR /app

ENV NODE_ENV production

COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./

RUN addgroup --gid 1001 --system nodejs
RUN adduser --uid 1001 --system nextjs

USER nextjs

EXPOSE 3000

ENV PORT 3000

CMD ["pnpm", "start"]
