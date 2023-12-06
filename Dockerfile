ARG REGISTRY_HOST_VAR
FROM ${REGISTRY_HOST_VAR}/proxy/library/python:3.11.4

ADD . .

RUN pip3 install -U -r requirements.txt

CMD ["python3","main.py"]