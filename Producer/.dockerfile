FROM python:3.12
WORKDIR /app

ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p /app/config && cp /app/Producer/config/headers.json /app/config/headers.json
CMD ["python", "-m","Producer.fetch_details"]