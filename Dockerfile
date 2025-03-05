# Use official Python image
FROM python:3.11

# Set working directory
WORKDIR /app

# Copy app files
COPY app.py requirements.txt /app/

# Install dependencies
RUN pip install -r requirements.txt

# Expose port 5000
EXPOSE 5000

# Start the app
CMD ["python", "app.py"]