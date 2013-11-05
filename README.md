D7024E-WebSync
==============

Distributed File Synchronization


## Setup:

### Dependencies:
  - RabbitMQ Server
  - Docker (Requires kernel 3.8 or above)
  - Python 2.7 
  - Python Packages:
    - Flask
    - Requests 
    - Pika
    
### Running the main application
The first step is to first change the working directory to the project folder and build the Docker image

```bash
cd D7024E-WebSync/
sudo docker build -t="<image name>" .
```
After that run the following python command to run the application (it will by default run on port 5000)

```bash
python FlaskManagementConsole/run.py <docker image name>
```

### Just running the file syncing client
To just run the file syncing client run the following python command

```bash
python FlaskWebServer/run.py <port> <ip-address to RabbitMQ-server>
```
