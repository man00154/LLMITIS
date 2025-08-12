# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Set the Gemini API key as an environment variable
ENV GEMINI_API_KEY="AIzaSyC_I9f8QTrGlZWzTEZXp6Ml4CM6yWXn5_g"

# Copy the requirements file into the container at /app
COPY requirements.txt ./

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code into the container at /app
COPY app.py ./

# Make port 8501 available to the world outside this container
EXPOSE 8501

# Run the streamlit application
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
