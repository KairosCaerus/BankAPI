import sqlite3


def clearDB(c):
    c.execute('''SELECT NAME FROM sqlite_master WHERE type="table"''')
    records = c.fetchall()
    for row in records:
        x = f'DROP TABLE {row[0]}'
        c.execute(x)


def initDB(c):
    clearDB(c)
    c.execute('''CREATE TABLE users (username text UNIQUE, password text, firstName text, lastName text)''')
    c.execute('''CREATE TABLE accounts (accountID integer UNIQUE, accountName text, owner text, pinNum integer, balance real)''')
    c.execute('''CREATE TABLE checkHistory (targetAccount integer, amount integer, imageOfCheck text)''')


connection = sqlite3.connect('bankdb.db')
cursor = connection.cursor()
initDB(cursor)
connection.close()
