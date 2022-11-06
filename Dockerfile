FROM python

RUN pip install \
    flask \
    psycopg2 \

COPY . /app/

WORKDIR /app

CMD [ "python3", "./main.py" ]