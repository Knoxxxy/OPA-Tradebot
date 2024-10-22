#!/bin/bash

# Set container name
CONTAINER_NAME="mongodb_OPA"

# Check if the MongoDB container is already running
if [ "$(docker ps -q -f name=$CONTAINER_NAME)" ]; then
    echo "MongoDB container ($CONTAINER_NAME) is already running."
else
    # Check if the container exists but is stopped
    if [ "$(docker ps -aq -f status=exited -f name=$CONTAINER_NAME)" ]; then
        echo "Starting existing MongoDB container..."
        docker start $CONTAINER_NAME
    else
        # Pull MongoDB image (if not already pulled) and run the container
        echo "Pulling MongoDB image..."
        docker pull mongo

        echo "Running MongoDB container..."
        docker run -d -p 27017:27017 --name $CONTAINER_NAME mongo
    fi
fi

# Verify that the container is running
if [ "$(docker ps -q -f name=$CONTAINER_NAME)" ]; then
    echo "MongoDB container is running on port 27017."
else
    echo "Failed to start MongoDB container."
fi