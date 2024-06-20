FROM python:3.11-slim-bullseye

COPY . /tmp/mtd/

RUN pip3 install --trusted-host pypi.python.org -r /tmp/mtd/requirements.txt /tmp/mtd

CMD ["python3", "-m", "mtd"]
