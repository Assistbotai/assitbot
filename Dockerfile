# Use Python 3.9 as the base image
FROM python:3.9

# Set the working directory inside the container
WORKDIR /app

# Install espeak (needed for pyttsx3)
RUN apt-get update && apt-get install -y espeak

# Copy all files from the local directory to the container
COPY . .

# Install dependencies from requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Expose port 8080 for Flask to run
EXPOSE 8080

# Start the chatbot application
CMD ["python", "Assistbot.py"]





