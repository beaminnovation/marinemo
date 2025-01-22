# Use the official Python image with version 3.9
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy all necessary files to the working directory
COPY . /app

# Install required Python packages
RUN pip install --no-cache-dir flask flask-cors joblib pandas scikit-learn==1.5.1 influxdb-client requests confluent-kafka
RUN chmod +x /app/start.sh

# Expose the port the app runs on
EXPOSE 5000
EXPOSE 1025

# Command to run the web application
CMD ["./start.sh"]
