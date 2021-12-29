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
RUN apt-get -y install --no-install-recommends wget
RUN apt-get -y install --no-install-recommends build-essential
RUN apt-get clean
RUN rm -rf /var/lib/apt/lists/*

# download and install pixlet
ENV PIXLET_VERSION 0.7.0
ENV PIXLET_TAR pixlet_${PIXLET_VERSION}_linux_amd64.tar.gz
RUN wget https://github.com/tidbyt/pixlet/releases/download/v$PIXLET_VERSION/$PIXLET_TAR
RUN tar -xvf $PIXLET_TAR
ENV PATH="$APP_HOME:${PATH}"

# install all packages from requirements.txt file
WORKDIR $APP_HOME
RUN pip install --no-cache-dir --requirement requirements.txt

# run the python service
CMD python tidbyt_display_service.py