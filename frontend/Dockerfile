# Use an official Node runtime as the base image
FROM node:14

# Set the working directory in the container to /app
WORKDIR /app

# Copy package.json and package-lock.json into the directory
COPY . .

# Install the application dependencies
RUN npm install

# Build the app
RUN npm run build


# Install serve to serve the build folder
RUN npm install -g serve

# The app is served on port 5000 by default
EXPOSE 3000

# Command to run the application
CMD ["serve", "-s", "build"]