# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the code into the container
COPY . /app

# Expose any port you need; typically the local web server may run on 8080 or similar
EXPOSE 8080

# Run the main script by default
CMD ["python", "main.py"]


##Steps to Deply the Docker Image
#1. Build the Docker Image
# docker build -t calendar_agent:latest .

#2. Run the Docker Image
# docker run -it -p 8080:8080 --name calendar_agent_container calendar_agent:latest

