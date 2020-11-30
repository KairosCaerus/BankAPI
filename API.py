import random
import flask
import sqlite3

from flask import request, jsonify

app = flask.Flask(__name__)
MAIN_DB = 'bankdb.db'


@app.route('/', methods=['GET'])
def home():
    return "You are monkey"


@app.route('/users/add', methods=['POST'])
def addUser():
    newUser = (
        request.args["username"],
        request.args["password"],
        request.args["firstname"],
        request.args["lastname"]
    )
    pin = request.args["pin"]

    conn = sqlite3.connect(MAIN_DB)
    c = conn.cursor()
    query = f'SELECT username FROM users WHERE username = ?'

    c.execute(query, (newUser[0],))

    if len(c.fetchall()) != 0:
        conn.close()
        return {'message': 'That user already exists', 'success': False}, 401

    c.execute('INSERT INTO users VALUES (?,?,?,?)', newUser)

    accountID = 0
    while True:
        accountID = random.randint(10 ** 8, 10 ** 9 - 1)

        query = f'SELECT accountID FROM accounts WHERE accountID = ?'
        c.execute(query, (accountID,))
        if len(c.fetchall()) == 0:
            break

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

    return usersToJSON(results), 200


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
    c.execute('UPDATE accounts SET balance=? WHERE accountID=?', (c.fetchone()[0] + amountDeposited, targetAccount,))
    conn.commit()

    conn.close()
    return {'message': 'Money Deposited', 'success': True}, 200


@app.route('/atm/withdraw', methods=['PUT'])
def withdrawCash():
    targetAccount = request.args['from']
    amountToWithdraw = int(request.args['amount'])

    conn = sqlite3.connect(MAIN_DB)
    c = conn.cursor()

    c.execute('SELECT balance FROM accounts WHERE accountID=?', (targetAccount,))
    currentAmount = c.fetchone()[0]

    if currentAmount < amountToWithdraw:
        conn.commit()
        conn.close()
        return {'message': 'There is not enough money in the account', 'success': False}, 401

    c.execute('UPDATE accounts SET balance=? WHERE accountID=?', (currentAmount - amountToWithdraw, targetAccount,))
    conn.commit()
    conn.close()

    return {'message': 'Money successful withdrawn', 'success': True}, 200


@app.route('/users/login', methods=['GET'])
def websiteLogIn():
    username = request.args['user']
    password = request.args['pass']

    conn = sqlite3.connect(MAIN_DB)
    c = conn.cursor()

    c.execute('SELECT * FROM users WHERE username=? AND password=?', (username, password,))

    result = c.fetchone()
    conn.close()

    if result is None:
        return {'message': 'Username or password is incorrect', 'success': False}, 401
    return {'message': 'Login successful', 'success': True}, 200


@app.route('/atm/login', methods=['GET'])
def atmLogin():
    username = request.args['user']
    pin = request.args['pin']

    conn = sqlite3.connect(MAIN_DB)
    c = conn.cursor()

    c.execute('SELECT * FROM accounts WHERE owner=? AND pinNum=?', (username, pin,))

    result = c.fetchall()
    conn.close()

    if len(result) == 0:
        return {'message': 'There are no accounts associated with this username and pin', 'success': False}, 401
    return accountsToJSON(result), 200


@app.route('/users/accounts', methods=['GET'])
def viewAccounts():
    username = request.args['user']

    conn = sqlite3.connect(MAIN_DB)
    c = conn.cursor()

    c.execute('SELECT * FROM accounts WHERE owner=?', (username,))

    result = c.fetchall()
    conn.close()
    return accountsToJSON(result), 200


@app.route('/users/accounts/updatePIN', methods=['PUT'])
def updatePIN():
    targetAccount = request.args['target']
    newPIN = request.args['pin']

    conn = sqlite3.connect(MAIN_DB)
    c = conn.cursor()

    c.execute('UPDATE accounts SET pinNum=? WHERE accountID=?', (newPIN, targetAccount,))

    conn.commit()
    conn.close()

    return {'message': 'PIN updated', 'success': True}, 200


@app.route('/users/accounts/new', methods=['POST'])
def openAccount():
    owner = request.args['owner']
    accName = request.args['name']
    pin = int(request.args['pin'])

    conn = sqlite3.connect(MAIN_DB)
    c = conn.cursor()

    accountID = 0
    while True:
        accountID = random.randint(10 ** 8, 10 ** 9 - 1)

        query = f'SELECT accountID FROM accounts WHERE accountID = ?'
        c.execute(query, (accountID,))
        if len(c.fetchall()) == 0:
            break

    c.execute('INSERT INTO accounts VALUES (?,?,?,?,?)', (accountID, accName, owner, pin, 0))

    conn.commit()
    conn.close()

    return {'message': f'Account successfully created. Account ID is {accountID}', 'accountID': accountID,
            'success': True}, 200


def accountsToJSON(target):
    results = []
    for row in target:
        dictForRow = {
            'accountID': row[0],
            'accountName': row[1],
            'owner': row[2],
            'balance': row[3]
        }
        results.append(dictForRow)
    return jsonify(results)


def usersToJSON(target):
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
