FROM python:3.10
LABEL maintainer="kkt"

ENV PYTHONUNBUFFERED 1

ENV PYTHONPATH="/shapi:$PYTHONPATH"
RUN apt-get update && apt-get install -y --no-install-recommends \
    unixodbc-dev \
    unixodbc \
    libpq-dev \
    libglib2.0-dev

COPY ./requirements.txt /tmp/requirements.txt
# COPY ./requirements.dev.txt /tmp/requirements.dev.txt

RUN python -m venv /py && \
    /py/bin/pip install --upgrade pip 
    # # 혹시나 이전 crontab 흔적 제거
RUN rm -rf /py/lib/python3.10/site-packages/crontab* 
# RUN apt-get install postgresql postgresql-client
RUN /py/bin/pip install --no-cache-dir -r /tmp/requirements.txt 
# RUN /py/bin/pip install --no-cache-dir python-crontab==3.2.0
# RUN rm -rf /py/lib/python3.10/site-packages/crontab* 

    
RUN rm -rf /tmp && \
    adduser \
        --disabled-password \
        --no-create-home \
        django


COPY ./uwsgi_docker /uwsgi
COPY . /shapi
WORKDIR /shapi
EXPOSE 9999

ENV PATH="/uwsgi:/py/bin:$PATH"

USER root


# CMD [ "uwsgi", "--ini", "/shapi/uwsgi_docker/uwsgi.ini" ]