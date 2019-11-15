FROM qgis/qgis:release-3_4


# This section taken on 2 July 2015 from
# https://docs.docker.com/examples/running_ssh_service/
# Sudo is needed by pycharm when it tries to pip install packages
RUN apt-get update -y; apt-get install -y openssh-server sudo
RUN mkdir /var/run/sshd
RUN echo 'root:docker' | chpasswd
# Comment out PermitRootLogin setting, whatever it is
RUN sed -i 's/^PermitRootLogin */#PermitRootLogin /' /etc/ssh/sshd_config
# Write out PermitRootLogin setting at the end
RUN echo "PermitRootLogin yes" >> /etc/ssh/sshd_config

# SSH login fix. Otherwise user is kicked off after login
RUN sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd

ENV NOTVISIBLE "in users profile"
RUN echo "export VISIBLE=now" >> /etc/profile


ADD REQUIREMENTS.txt /REQUIREMENTS.txt
ADD REQUIREMENTS_TESTING.txt /REQUIREMENTS_TESTING.txt

RUN pip3 install -r /REQUIREMENTS.txt
RUN pip3 install -r /REQUIREMENTS_TESTING.txt

ADD entrypoint.sh /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]

CMD ["/usr/sbin/sshd", "-D"]