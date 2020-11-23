import random
import flask
import sqlite3

from flask import request, jsonify

app = flask.Flask(__name__)
MAIN_DB = 'testdb.db'


@app.route('/', methods=['GET'])
def home():
    return "You are monkey"


@app.route('/users/add', methods=['POST'])
def addUser():
    conn = sqlite3.connect(MAIN_DB)
    c = conn.cursor()
    newUser = (
        request.args["username"],
        request.args["password"],
        request.args["firstname"],
        request.args["lastname"]
    )

    query = f'SELECT username FROM users WHERE username = ?'
    c.execute(query, (request.args["username"],))
    if len(c.fetchall()) != 0:
        conn.close()
        return {'message': 'That user already exists'}, 401

    c.execute('INSERT INTO users VALUES (?,?,?,?)', newUser)

    accountID = random.randint(10**8, 10**9 - 1)
    print(accountID)
    c.execute('INSERT INTO accounts VALUES (?,?,?,?,?)', (accountID, 'Checking', newUser[0], 1111, 0))
    conn.commit()
    conn.close()

    return {'message': 'Account successfully created'}, 200


@app.route('/users/all', methods=['GET'])
def getAllUsers():
    conn = sqlite3.connect(MAIN_DB)
    c = conn.cursor()

    c.execute('SELECT * FROM users')
    results = c.fetchall()

    conn.close()

    return toJSON(results), 200


def toJSON(target):
    results = []
    for row in target:
        dictForRow = {
            'username': row[0],
            'password': row[1],
            'firstname': row[2],
            'lastname': row[3]
        }
        results.append(dictForRow)
    return jsonify(results)


app.run()
