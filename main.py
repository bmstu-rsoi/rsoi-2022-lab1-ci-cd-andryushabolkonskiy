import psycopg2
import flask
from dataclasses import dataclass
import json
from typing import Dict, List, Union

conn = psycopg2.connect(dbname='d1197oq2du464e', user='ifbyzhwjgemnpe', 
                        password='071231d4f79ca1acfabd3e80971b37ab6ef12bd36d8ed4ac2cdcfe5eb0bcacd8', host='ec2-3-219-135-162.compute-1.amazonaws.com')

cursor = conn.cursor()

app = flask.Flask(__name__)

def cleanNones(o):
    return {k: v for k,
            v in o.__dict__.items() if v is not None}

class ApiMessage:
    def toJSON(obj):
        return json.dumps(obj, separators=(',', ':'),
                          default=cleanNones)

def arrToJson(arr: List[ApiMessage]):
    return json.dumps([cleanNones(e) for e in arr], separators=(',', ':'))

@dataclass
class PersonResponse(ApiMessage):
    id: int
    name: str
    age: Union[int, None]
    address: Union[str, None]
    work: Union[str, None]

def getPersons() -> List[PersonResponse]:
    #with conn.cursor() as cursor:
    cursor.execute('SELECT id, name, age, address, work FROM pers')
    persons_data = [PersonResponse(*e) for e in cursor]
    return persons_data

@app.route('/api/v1/persons', methods=['GET', 'POST'])
def personsRoute():
    if flask.request.method == 'GET':
        persons = getPersons()
        resp = flask.Response(arrToJson(persons))
        resp.headers['Content-Type'] = 'application/json'
        return resp

port = 8080
app.run(host="0.0.0.0", port=port)