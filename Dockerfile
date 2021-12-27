# load lightweight Python
FROM python:3.7-slim

# allow statements and log messages to immediately appear in the Stackdriver logs
ENV PYTHONUNBUFFERED True

# copy local code to the container image
ENV APP_HOME /app
WORKDIR $APP_HOME
COPY . .

# update and upgrade
RUN apt-get update
RUN apt-get -y upgrade

# install packages without the recommended packages
RUN apt-get -y install --no-install-recommends curl
RUN apt-get -y install --no-install-recommends build-essential
RUN apt-get clean
RUN rm -rf /var/lib/apt/lists/*

# install all packages from requirements.txt file
WORKDIR $APP_HOME
RUN pip install --no-cache-dir --requirement requirements.txt

# Run the web service on container startup. Here we use the gunicorn
# webserver, with one worker process and 8 threads.
# For environments with multiple CPU cores, increase the number of workers
# to be equal to the cores available.
# Timeout is set to 0 to disable the timeouts of the workers to allow Cloud Run
# to handle instance scaling.
CMD exec gunicorn --bind $PORT --workers 1 --threads 8 --timeout 0 main:app