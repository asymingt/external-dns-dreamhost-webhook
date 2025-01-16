FROM python:3.12-alpine
COPY webhook.py /root
COPY requirements.txt /root
WORKDIR /root
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
CMD ["python", "webhook.py"]