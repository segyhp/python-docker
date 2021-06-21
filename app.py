from flask import Flask
from influxdb import InfluxDBClient

import mysql.connector
import json
import requests
import time
import datetime
import math
import pprint
import os
import signal
import sys

app = Flask(__name__)

client = None
dbname = 'pyexample'
measurement = 'brushEvents'


@app.route('/')
def hello_world():
    return 'Hello World';


@app.route('/widgets')
def get_widgets():
    mydb = mysql.connector.connect(
        host="mysqldb",
        user="root",
        password="password",
        database="inventory"
    )
    cursor = mydb.cursor()

    cursor.execute("SELECT * FROM widgets")

    row_headers = [x[0] for x in cursor.description]  # this will extract row headers

    results = cursor.fetchall()
    json_data = []
    for result in results:
        json_data.append(dict(zip(row_headers, result)))

    cursor.close()

    return json.dumps(json_data)


@app.route('/initdb')
def db_init():
    mydb = mysql.connector.connect(
        host="mysqldb",
        user="root",
        password="password"
    )
    cursor = mydb.cursor()

    cursor.execute("DROP DATABASE IF EXISTS inventory")
    cursor.execute("CREATE DATABASE inventory")
    cursor.close()

    mydb = mysql.connector.connect(
        host="mysqldb",
        user="root",
        password="password",
        database="inventory"
    )
    cursor = mydb.cursor()

    cursor.execute("DROP TABLE IF EXISTS widgets")
    cursor.execute("CREATE TABLE widgets (name VARCHAR(255), description VARCHAR(255))")
    cursor.close()

    return 'init database'


# Section for Influx DB

def db_exists():
    '''returns True if the database exists'''
    dbs = client.get_list_database()
    for db in dbs:
        if db['name'] == dbname:
            return True
    return False


def wait_for_server(host, port, nretries=5):
    '''wait for the server to come online for waiting_time, nretries times.'''
    url = 'http://{}:{}'.format(host, port)
    waiting_time = 1
    for i in range(nretries):
        try:
            requests.get(url)
            return
        except requests.exceptions.ConnectionError:
            print('waiting for', url)
            time.sleep(waiting_time)
            waiting_time *= 2
            pass
    print('cannot connect to', url)
    sys.exit(1)


def connect_db(host, port, reset):
    '''connect to the database, and create it if it does not exist'''
    global client
    print('connecting to database: {}:{}'.format(host, port))
    client = InfluxDBClient(host, port, retries=5, timeout=1)
    wait_for_server(host, port)
    create = False
    if not db_exists():
        create = True
        print('creating database...')
        client.create_database(dbname)
    else:
        print('database already exists')
    client.switch_database(dbname)
    if not create and reset:
        client.delete_series(measurement=measurement)


def measure(nmeas):
    '''insert dummy measurements to the db.
    nmeas = 0 means : insert measurements forever.
    '''
    i = 0
    if nmeas == 0:
        nmeas = sys.maxsize
    for i in range(nmeas):
        x = i / 10.
        y = math.sin(x)
        data = [{
            'measurement': measurement,
            'time': datetime.datetime.now(),
            'tags': {
                'x': x
            },
            'fields': {
                'y': y
            },
        }]
        client.write_points(data)
        pprint.pprint(data)
        time.sleep(1)


def get_entries():
    '''returns all entries in the database.'''
    results = client.query('select * from {}'.format(measurement))
    # we decide not to use the x tag
    return list(results[(measurement, None)])


if __name__ == "__main__":
    app.run(host='0.0.0.0')


#InfluxDB main section
if __name__ == '__main__bak':
    import sys

    from optparse import OptionParser

    parser = OptionParser('%prog [OPTIONS] <host> <port>')
    parser.add_option(
        '-r', '--reset', dest='reset',
        help='reset database',
        default=False,
        action='store_true'
    )
    parser.add_option(
        '-n', '--nmeasurements', dest='nmeasurements',
        type='int',
        help='reset database',
        default=0
    )

    options, args = parser.parse_args()
    if len(args) != 2:
        parser.print_usage()
        print('please specify two arguments')
        sys.exit(1)
    host, port = args
    connect_db(host, port, options.reset)


    def signal_handler(sig, frame):
        print()
        print('stopping')
        pprint.pprint(get_entries())
        sys.exit(0)


    signal.signal(signal.SIGINT, signal_handler)

    measure(options.nmeasurements)

    pprint.pprint(get_entries())
