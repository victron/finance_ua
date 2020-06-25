# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.8-slim-buster

EXPOSE 9080

# Keeps Python from generating .pyc files in the container
# https://stackoverflow.com/questions/59732335/is-there-any-disadvantage-in-using-pythondontwritebytecode-in-docker
ENV PYTHONDONTWRITEBYTECODE 1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED 1

# Install pip requirements
ADD requirements.txt .
RUN apt-get update \
 && apt-get install -y gcc \
 && apt-get install -y rsyslog
RUN python -m pip install -r requirements.txt

WORKDIR /app
ADD . /app

# Switching to a non-root user, please refer to https://aka.ms/vscode-docker-python-user-rights
RUN useradd appuser && chown -R appuser /app
USER appuser

EXPOSE 9080/tcp
ENTRYPOINT [ "uwsgi", "--ini", "config/uwsgi.ini" ]
# CMD [ "executable" ]

# NOTES: 
# docker run --name spiders -d --env secret_berlox='smth' --env secret_api='smth'  --net=host -p 127.0.0.1:9080:9080/tcp victron/finance_ua/spiders:latest


