#!/bin/bash

# 서비스 이름
SERVICE_NAME="automation.service"

echo "Stopping $SERVICE_NAME..."
sudo systemctl stop $SERVICE_NAME

echo "Starting $SERVICE_NAME..."
sudo systemctl start $SERVICE_NAME

echo "$SERVICE_NAME has been restarted successfully."

