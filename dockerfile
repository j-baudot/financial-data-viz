# Use an official Python runtime as a parent image
FROM python:3.11

# Set the working directory in the container
WORKDIR /app

# Copy the wait script and requirements file into the container
COPY wait-for-it.sh ./
COPY requirements.txt ./

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make the wait script executable
RUN chmod +x ./wait-for-it.sh

# Copy the rest of the application code into the container
COPY . .