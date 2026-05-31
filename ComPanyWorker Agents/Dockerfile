# GIANTECH EMPIRE - SCRAPER PRODUCTION DOCKERFILE
# We use Node 20 bullseye-slim as base to properly support Playwright browser dependencies
FROM mcr.microsoft.com/playwright:v1.44.0-jammy AS runner

WORKDIR /app

# Set production environment variables
ENV NODE_ENV=production
ENV PORT=3000
ENV DATABASE_PATH=/data/leads.db

# Copy package descriptors
COPY package*.json ./

# Install packages
RUN npm ci --only=production

# Copy source trees
COPY . .

# Expose server port
EXPOSE 3000

# Run entrypoint script
CMD ["node", "server.js"]
