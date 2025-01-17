FROM python:3.12-alpine
COPY requirements.txt /root
WORKDIR /root
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
COPY webhook.py /app/webhook.py
WORKDIR /app
USER 8675:8675
EXPOSE 8888
CMD ["python", "webhook.py"]
