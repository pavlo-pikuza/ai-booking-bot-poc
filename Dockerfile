FROM python:3.11

WORKDIR /app

RUN apt-get update && apt-get install -y sqlite3

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

RUN python populate_db.py

EXPOSE 5000

CMD ["python", "app.py"]