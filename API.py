import os
import random
import flask
import sqlite3

from flask import request, jsonify, url_for
from flask_cors import CORS

app = flask.Flask(__name__)
CORS(app)
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
        return {'message': 'That user already exists', 'success': False}, 200

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
    result = c.fetchone()
    if result is None:
        conn.close()
        return {'message': 'Target Account does not exist', 'success': False}, 401
    newCashAmountSource = origCashAmount - transferAmount
    newCashAmountTarget = result[0] + transferAmount
    c.execute('UPDATE accounts SET balance=? WHERE accountID=?', (round(newCashAmountSource, 2), sourceAccount,))
    c.execute('UPDATE accounts SET balance=? WHERE accountID=?', (round(newCashAmountTarget, 2), targetAccount,))
    conn.commit()

    conn.close()
    return {'message': 'Money Transferred', 'success': True}, 200


@app.route('/users/deposit', methods=['POST'])
def depositCash():
    targetAccount = request.args['to']
    amountDeposited = float(request.args['amount'])
    uploadedImage = request.files['file']

    conn = sqlite3.connect(MAIN_DB)
    c = conn.cursor()

    c.execute('SELECT balance FROM accounts WHERE accountID=?', (targetAccount,))
    result = c.fetchone()
    if result is None:
        conn.close()
        return {'message': 'Account does not exist', 'success': True}, 401

    filepath = ''
    while True:
        filepath = os.path.join('./bankChecks',
                                f'{random.randint(0, 10 ** 6 - 1)}.{uploadedImage.filename.split(".")[1]}')
        if not os.path.exists(filepath):
            break

    uploadedImage.save(filepath)

    c.execute('UPDATE accounts SET balance=? WHERE accountID=?', (round(result[0] + amountDeposited, 2), targetAccount,))
    c.execute('INSERT INTO checkHistory VALUES (?, ?, ?)', (targetAccount, amountDeposited, filepath,))
    conn.commit()

    conn.close()
    return {'message': 'Money Deposited', 'success': True}, 200


@app.route('/atm/withdraw', methods=['PUT'])
def withdrawCash():
    user = request.args['user']
    targetAccount = request.args['from']
    amountToWithdraw = float(request.args['amount'])

    conn = sqlite3.connect(MAIN_DB)
    c = conn.cursor()

    c.execute('SELECT balance FROM accounts WHERE accountID=? AND owner = ?', (targetAccount, user,))
    result = c.fetchone()

    if result is None:
        conn.close()
        return {'message': 'Account does not exist', 'success': False}, 401

    currentAmount = result[0]

    if currentAmount < amountToWithdraw:
        conn.commit()
        conn.close()
        return {'message': 'There is not enough money in the account', 'success': False}, 401

    c.execute('UPDATE accounts SET balance=? WHERE accountID=?', (round(currentAmount - amountToWithdraw, 2), targetAccount,))
    conn.commit()
    conn.close()

    return {'message': 'Money successfully withdrawn', 'success': True}, 200


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

    return {'message': 'Success, you have been logged in.', 'success': True}, 200


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

@app.route('/users/accounts/close', methods=['DELETE'])
def closeAccount():
    accountID = request.args['target']
    user = request.args['user']
    pin = request.args['pin']

    conn = sqlite3.connect(MAIN_DB)
    c = conn.cursor()

    c.execute('SELECT * FROM accounts WHERE accountID = ? AND pinNum = ? AND owner = ?', (accountID, pin, user,))
    result = c.fetchone()
    if result is None:
        conn.close()
        return {'message': 'That account does not exist', 'success': False}

    if result[4] > 0:
        conn.close()
        return {'message': 'The account still contains money. Please withdraw all money first', 'success': False}

    c.execute('DELETE FROM accounts WHERE accountID = ?', (accountID,))

    conn.commit()
    conn.close()
    return {'message': 'Account successfully closed', 'success': True}

@app.route('/users/accounts/owns', methods=['GET'])
def checkAccountValid():
    owner = request.args['user']
    accToCheck = request.args['id']

    conn = sqlite3.connect(MAIN_DB)
    c = conn.cursor()

    c.execute('SELECT * FROM accounts WHERE accountID = ? AND owner = ?', (accToCheck, owner,))

    result = c.fetchone()

    conn.close()

    if result is None:
        return {'message': 'You do not own that account', 'success': False}
    return {'message': 'No issues', 'success': True}


@app.route('/users/delete', methods=['DELETE'])
def deleteUser():
    username = request.args['user']
    password = request.args['pass']

    conn = sqlite3.connect(MAIN_DB)
    c = conn.cursor()

    c.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password,))
    results = c.fetchone()
    if results is None:
        conn.close()
        return {'message': 'Incorrect credentials provided', 'success': False}

    c.execute('SELECT * FROM accounts WHERE owner = ?', (username,))
    results = c.fetchall()
    for result in results:
        if result[4] > 0:
            conn.close()
            return {'message': f'Account {result[0]} still has money in it. Please withdraw all cash before deleting account', 'success': False}, 401

    c.execute('DELETE FROM accounts WHERE owner = ?', (username,))
    c.execute('DELETE FROM users WHERE username = ?', (username,))
    conn.commit()
    conn.close()

    return {'message': 'The user and associated accounts were deleted', 'success': True}


def accountsToJSON(target):
    results = []
    results.append({'message' : 'Log in Successful', 'success': True})
    for row in target:
        dictForRow = {
            'Account ID': row[0],
            'Name': row[1],
            #'owner': row[2],
            'balance': f'${row[4]:.2f}'
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
