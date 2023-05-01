# Python and Node.js image
FROM nikolaik/python-nodejs:python3.10-nodejs20

WORKDIR /app

RUN python -m venv /venv
ENV PATH /venv/bin:$PATH

COPY log_parsing /app/log_parsing
COPY ./requirements.txt /app
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY ./setup.cfg /app
COPY ./pyproject.toml /app
RUN pip install -e /app/
COPY dashboard/package*.json ./dashboard/
RUN cd dashboard && npm ci


COPY . .

RUN cd dashboard && npm run build:prod

CMD ["/venv/bin/python", "dashboard/app.py"]
