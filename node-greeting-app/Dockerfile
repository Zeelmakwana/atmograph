# Use a Node image already present locally
FROM node:20-alpine   # choose any Node image you have locally

# Set working directory in container
WORKDIR /usr/src/app

# Copy everything from your project folder into container
COPY . .

# Expose port 3000 so container can communicate with host
EXPOSE 3000

# Command to run your app
CMD ["node", "app.js"]
