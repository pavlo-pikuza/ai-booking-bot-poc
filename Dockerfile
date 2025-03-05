FROM python:3.11

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY populate_db.py /app/populate_db.py
RUN python populate_db.py

COPY . /app

EXPOSE 5000

CMD ["python", "app.py"]