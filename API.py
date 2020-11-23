import flask
import sqlite3

from flask import request

app = flask.Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    return "You are monkey"

@app.route('/users/add', methods=['POST'])
def addUser():
    conn = sqlite3.connect('testdb.db')
    c = conn.cursor()
    newUser = (
        request.args["username"],
        request.args["password"],
        request.args["firstname"],
        request.args["lastname"]
    )

    query = f'SELECT username FROM users WHERE username = ?'
    c.execute(query, (request.args["username"], ))
    if len(c.fetchall()) != 0:
        conn.close()
        return "That user already exists."

    c.execute('INSERT INTO users VALUES (?,?,?,?)', newUser)
    conn.commit()
    conn.close()

    return "Something happened"


app.run()