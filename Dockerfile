FROM websync

RUN apt-get update
RUN apt-get install -y python python-setuptools curl unzip git-core
RUN easy_install pip 
RUN pip install flask
RUN pip install pika
RUN pip install requests

RUN curl -LOk https://github.com/AnotherDay/D7024E-WebSync/archive/develop.zip && unzip develop.zip && rm develop.zip && rm -r D7024E-WebSync-develop/FlaskManagementConsole/
ENV PYTHONPATH /D7024E-WebSync-develop/FlaskWebServer/blueprints/
