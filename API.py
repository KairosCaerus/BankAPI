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
        return "That user already exists."

    c.execute('INSERT INTO users VALUES (?,?,?,?)', newUser)
    conn.commit()
    conn.close()

    return "Account successfully created"


@app.route('/users/all', methods=['GET'])
def getAllUsers():
    conn = sqlite3.connect(MAIN_DB)
    c = conn.cursor()

    c.execute('SELECT * FROM users')
    results = c.fetchall()

    conn.close()

    print(results)

    return toJSON(results)

def toJSON(target):
    results = []
    for row in target:
        dictForRow = {
            'username' : row[0],
            'password' : row[1],
            'firstname' : row[2],
            'lastname' : row[3]
        }
        results.append(dictForRow)
    return jsonify(results)

app.run()
