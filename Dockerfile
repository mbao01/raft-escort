# set base image (host OS)
FROM python:3.8.10-buster

# set the working directory in the container
WORKDIR /raft

# copy the dependencies file to the working directory
COPY requirements.txt /raft/requirements.txt

# install dependencies
RUN pip install --timeout=9000000 -r requirements.txt

RUN echo 'export CONTAINER_IP="$(hostname -i)"' >> ~/.bashrc

# copy the content of the local src directory to the working directory
COPY . /raft

EXPOSE 8080

# command to run on container start
CMD . ~/.bashrc && python -m src.api.api
