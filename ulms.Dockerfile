FROM python:3.8

#Set work directory for container
WORKDIR /ulms-service

#Copy necessary dependecy from host to container
COPY requirements.txt .

#Run installation of necessary package
RUN python -m pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Install tools for debugging (using vi/vim/nano)
RUN apt update && apt install -y \
    vim \
    iputils-ping \
    && rm -rf /var/lib/apt/lists/*

RUN touch /root/.bashrc \
    && echo "export LS_OPTIONS='--color=auto'"  >> /root/.bashrc \
    && echo "eval \"\`dircolors\`\""            >> /root/.bashrc \
    && echo "alias ls='ls \$LS_OPTIONS'"        >> /root/.bashrc \
    && echo "alias ll='ls \$LS_OPTIONS -l'"     >> /root/.bashrc \
    && echo "alias l='ls \$LS_OPTIONS -lA'"     >> /root/.bashrc

# Copy all content from host to container
COPY . .

# Set default command when run the container
CMD ["python", "-m", "flask", "run", "--host=0.0.0.0"]
#CMD ["python"]
#CMD ["gunicorn", "-w", "3", "-b", "0.0.0.0:5000", "wsgi:app2"]
#CMD ["gunicorn", "-w", "3", "-b", "0.0.0.0:5000", "web_service:app"]



