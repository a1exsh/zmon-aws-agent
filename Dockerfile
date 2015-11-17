FROM zalando/python:15.01.03

RUN apt-get install -y supervisor

ADD requirements.txt /requirements.txt
RUN pip install --upgrade -r /requirements.txt

ADD run.sh /run.sh
ADD start.sh /start.sh

ADD supervisord.conf /etc/supervisord.conf

RUN touch /etc/entity_service_url
RUN chmod uog+w /etc/entity_service_url

ADD scm-source.json /scm-source.json

ADD zmon_agent /zmon_agent

CMD ["bash", "start.sh"]
