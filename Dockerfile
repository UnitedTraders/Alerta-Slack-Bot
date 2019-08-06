FROM python:3.7-stretch
ENV PYTHONUNBUFFERED 1

COPY requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

COPY src /app/src
COPY alerta_bot.conf /app/alerta_bot.conf

EXPOSE 8086

WORKDIR /app/src

CMD ["python", "app.py"]