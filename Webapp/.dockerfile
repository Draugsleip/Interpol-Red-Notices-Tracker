FROM python:3.12
WORKDIR /app

ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p /app/config && cp /app/Webapp/config/headers.json /app/config/headers.json
ENV FLASK_APP=Webapp.webapp:app
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]
