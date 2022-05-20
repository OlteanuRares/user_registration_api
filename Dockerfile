FROM python:3.7.6

ENV PYTHONUNBUFFERED 1

ADD . /src
WORKDIR /src

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

EXPOSE 8000
