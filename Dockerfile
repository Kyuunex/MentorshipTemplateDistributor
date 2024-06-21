FROM python:3.11-slim-bullseye

WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip install --trusted-host pypi.python.org --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "-m", "mtd"]
