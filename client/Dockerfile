# Use official Node image
FROM node:20-slim

WORKDIR /app

# Install dependencies (this will be done later when we actually build the React app)
# COPY package.json package-lock.json ./
# RUN npm install

# Copy source code
COPY . .

# Expose port
EXPOSE 3000

# Placeholder for dev command
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
