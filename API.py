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
        return {'message': 'That user already exists', 'success': False}, 401

    c.execute('INSERT INTO users VALUES (?,?,?,?)', newUser)

    accountID = 0
    while True:
        accountID = random.randint(10**8, 10**9 - 1)

        query = f'SELECT accountID FROM accounts WHERE accountID = ?'
        c.execute(query, (accountID,))
        if len(c.fetchall()) == 0:
            break

    pin = request.args["pin"]

    c.execute('INSERT INTO accounts VALUES (?,?,?,?,?)', (accountID, 'Checking', newUser[0], pin, 0))
    conn.commit()
    conn.close()

    return {'message': 'Account successfully created', 'success': True}, 200


@app.route('/users/all', methods=['GET'])
def getAllUsers():
    conn = sqlite3.connect(MAIN_DB)
    c = conn.cursor()

    c.execute('SELECT * FROM users')
    results = c.fetchall()

    conn.close()

    return toJSON(results), 200

@app.route('/users/transfer', methods=['PUT'])
def transferCash():
    sourceAccount = request.args['from']
    targetAccount = request.args['to']
    transferAmount = int(request.args['cash'])

    conn = sqlite3.connect(MAIN_DB)
    c = conn.cursor()

    c.execute('SELECT balance FROM accounts WHERE accountID=?', (sourceAccount,))
    origCashAmount = c.fetchone()[0]
    if transferAmount > origCashAmount:
        conn.close()
        return {'message': 'Source Account doesnt have enough cash', 'success': False}, 401

    c.execute('SELECT balance FROM accounts WHERE accountID=?', (targetAccount,))
    newCashAmountSource = origCashAmount - transferAmount
    newCashAmountTarget = c.fetchone()[0] + transferAmount
    c.execute('UPDATE accounts SET balance=? WHERE accountID=?', (newCashAmountSource, sourceAccount,))
    c.execute('UPDATE accounts SET balance=? WHERE accountID=?', (newCashAmountTarget, targetAccount,))
    conn.commit()

    conn.close()
    return {'message': 'Money Transferred', 'success': True}, 200

@app.route('/users/deposit', methods=['PUT'])
def depositCash():
    targetAccount = request.args['to']
    amountDeposited = int(request.args['amount'])

    conn = sqlite3.connect(MAIN_DB)
    c = conn.cursor()

    c.execute('SELECT balance FROM accounts WHERE accountID=?', (targetAccount,))
    c.execute('UPDATE accounts SET balance=? WHERE accountID=?', (c.fetchone()[0]+amountDeposited, targetAccount,))
    conn.commit()

    conn.close()
    return {'message': 'Money Deposited', 'success': True}, 200



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
