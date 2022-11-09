import os
import sys
import psycopg2
import flask
import json

from urllib.request import Request
#from api_messages import *
from flask import abort
from dataclasses import dataclass
from typing import Dict, List, Union

#Подключение к БД --- ОК
conn = psycopg2.connect(dbname='d1197oq2du464e', user='ifbyzhwjgemnpe', 
                        password='071231d4f79ca1acfabd3e80971b37ab6ef12bd36d8ed4ac2cdcfe5eb0bcacd8', host='ec2-3-219-135-162.compute-1.amazonaws.com')

cursor = conn.cursor()

app = flask.Flask(__name__)

class ApiMessage:
    def toJSON(obj):
        return json.dumps(obj, separators=(',', ':'),
                          default=cleanNones)

def cleanNones(o):
    return {k: v for k,
            v in o.__dict__.items() if v is not None}

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
    cursor.execute('SELECT id, name, age, address, work FROM pers')
    persons_data = [PersonResponse(*e) for e in cursor]
    return persons_data

@dataclass
class ErrorResponse(ApiMessage):
    msg: str

@dataclass
class ValidationErrorResponse(ApiMessage):
    msg: str
    errors: Dict[str, str]

@dataclass
class PersonRequest(ApiMessage):
    name: str
    age: Union[int, None]
    address: Union[str, None]
    work: Union[str, None]

def parseInt32(s: str):
    try:
        val = int(s)
    except:
        return None
    return val

def parsePersonRequest(request: Request) -> Union[PersonRequest, None]:
    if not request.is_json:
        return None
    if request.json.get("name", None) == None:
        return None
    return PersonRequest(
        name=request.json.get("name"),
        age=request.json.get("age"),
        address=request.json.get("address"),
        work=request.json.get("work"),
    )

# работает 
def getOnePerson(id: int) -> Union[PersonResponse, None]:
    cursor.execute(
        'SELECT id, name, age, address, work FROM pers WHERE id = %s', (id,))
    person_data = cursor.fetchone()
    if person_data != None:
        return PersonResponse(*person_data)
    else:
        return None

def createNewPerson(person: PersonRequest) -> int:
    cursor.execute('INSERT INTO pers(id, name, age, address, work)' +
                'VALUES (DEFAULT, %s, %s, %s, %s)' +
                'RETURNING id',
                (person.name, person.age, person.address, person.work))
    conn.commit()
    row = cursor.fetchone()
    return row[0]

def removePerson(id: int):
    cursor.execute('DELETE FROM pers WHERE id = %s', (id,))
    conn.commit()

def patchPerson(id: int, person: PersonRequest) -> Union[PersonResponse, None]:
    params = [person.name]
    if person.age != None:
        params.append(person.age)
    if person.address != None:
        params.append(person.address)
    if person.work != None:
        params.append(person.work)
    params.append(id)
    cursor.execute('UPDATE persons SET name = %s' +
                    (', age = %s' if person.age != None else '') +
                    (', address = %s' if person.address != None else '') +
                    (', work = %s' if person.work != None else '') +
                    'WHERE id = %s', params)
    conn.commit()

    return getOnePerson(id)

# Получить инфу обо всех записях --- ОК
@app.route('/api/v1/persons', methods=['GET', 'POST'])
def personsRoute():
    if flask.request.method == 'GET':
        persons = getPersons()
        resp = flask.Response(arrToJson(persons), status = 200)
        resp.headers['Content-Type'] = 'application/json'
        return resp

    elif flask.request.method == 'POST':
        personRequest = parsePersonRequest(flask.request)
        if personRequest == None:
            abort(404)

        newId = createNewPerson(personRequest)
        resp = flask.Response('', status = 201)
        resp.headers['Location'] = f'/api/v1/persons/{newId}'
        return resp
    else:
        abort(500)


@app.route('/api/v1/persons/<id>', methods=['GET', 'PATCH', 'DELETE'])
def personRoute(id):
    int_id = parseInt32(id)
    if int_id == None:
        abort(404)

    if flask.request.method == 'GET':
        person = getOnePerson(int_id)
        if person != None:
            resp = flask.Response(person.toJSON(), status = 200)
            resp.headers['Content-Type'] = 'application/json'
            return resp
        else:
            abort(404)

    elif flask.request.method == 'PATCH':
        personRequest = parsePersonRequest(flask.request)
        if personRequest == None:
            abort(404)

        person = patchPerson(int_id, personRequest)
        if person != None:
            abort(200)
            #resp = flask.Response(person.toJSON(), status.HTTP_200_OK)
            #resp.headers['Content-Type'] = 'application/json'
            #return resp
        else:
            abort(404)
            #return flask.Response(
            #    ErrorResponse(msg=f'There is no person with id {id}').toJSON(),
            #    status.HTTP_404_NOT_FOUND,
            #)

    elif flask.request.method == 'DELETE':
        removePerson(int_id)

    else:
        abort(404)

port = 8080
herokuPort = os.environ.get('PORT')
if herokuPort != None:
    port = herokuPort
if len(sys.argv) > 1:
    port = int(sys.argv[1])

app.run(host="0.0.0.0", port=port)