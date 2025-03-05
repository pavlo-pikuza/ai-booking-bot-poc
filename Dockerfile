FROM python:3.11

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

RUN python populate_db.py || echo "⚠️ Warning: Database population failed, continuing..."

EXPOSE 5000

CMD ["python", "app.py"]