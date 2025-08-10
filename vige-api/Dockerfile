FROM python:3.10

ARG PIP_INDEX_URL
ENV PIP_INDEX_URL=${PIP_INDEX_URL:-https://mirrors.aliyun.com/pypi/simple/}

RUN mkdir /vige
# https://github.com/pypa/pipenv/issues/2924
# https://github.com/pypa/pipenv/issues/2871
RUN pip install pipenv==2023.11.14
RUN pip install pip==20.2.3

COPY Pipfile /vige
COPY Pipfile.lock /vige
WORKDIR /vige
RUN pipenv install --system --deploy

COPY . /vige
WORKDIR /vige
RUN pip install -e .

EXPOSE 8000
ENV WEB_CONCURRENCY=4 WORKER_CONCURRENCY=4
VOLUME ["/vige/local_config.env"]
ENTRYPOINT ["./entrypoint.sh"]
CMD ["web"]

# run web:
#    docker run vige web
# run worker:
#    docker run vige worker
# enter container
#    docker exec -it vige-container bash
