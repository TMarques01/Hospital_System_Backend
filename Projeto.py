import flask
import logging
import psycopg2
import datetime
import calendar
import time
import jwt
import random

import hashlib 
from flask import jsonify, request

app = flask.Flask(__name__)

StatusCodes = {
    'success': 200,
    'api_error': 400,
    'internal_error': 500
}

def db_connection():
    db = psycopg2.connect(
        user='aulaspl',
        password='aulaspl',
        host='localhost',
        port='5432',
        database='projeto'
    )

    return db

@app.route('/')
def landing_page():
    return """

    Hello World (Python Native)!  <br/>
    <br/>
    Check the sources for instructions on how to use the endpoints!<br/>
    <br/>
    BD 2022 Team<br/>
    <br/>
    """

@app.route("/register/patient", methods=["POST"])
def register_patient():

    try:
        payload = request.get_json()
    except:
        return jsonify({
            "status": StatusCodes['api_error'],
            "error": "No json"
        })

    message = {}

    if "id" in payload and "nome" in payload and "contact" in payload and "email" in payload and "address" in payload and "password" in payload and "username" in payload and "historic" in payload:
        logger.debug(f'POST /projeto/register/patient - payload: {payload}')

        id = payload["id"]
        nome = payload["nome"]
        contact = payload["contact"]
        email = payload["email"]
        address = payload["address"]
        password = hashlib.sha256(payload["password"].enconde()).hexdigest() # encode the message
        username = payload["username"]
        historic = payload["historic"]

        get_id = "SELECT id FROM person WHERE id = %d"
        values_id = (id,)
        get_contact = "SELECT contact FROM person WHERE contact = %d"
        values_contact = (contact,)
        get_email =  "SELECT email FROM person WHERE email like %s"
        values_email = (email,)
        get_username = "SELECT username FROM person WHERE username like %s"
        values_username = (username,)

        try:
            with db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(get_id, values_id)

                    if cursor.rowcount == 1:
                        cursor.execute(get_contact, values_contact)

                        if cursor.rowcount == 1:
                            cursor.execute(get_email, values_email)
                    else:

                        message["status"] = StatusCodes['api_error']
                        message["error"] = "ID already exists!"

        except (Exception, psycopg2.DatabaseError) as error:
            return jsonify({
                "status": StatusCodes['internal_error'],
                "error": str(error)
            })
        
            # an error occurred, rollback
            conn.rollback()

        finally:
            if conn is not None:
                conn.close()

    return jsonify(message)




if __name__ == '__main__':

    # set up logging
    logging.basicConfig(filename='log_file.log')
    logger = logging.getLogger('logger')
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    # create formatter
    formatter = logging.Formatter('%(asctime)s [%(levelname)s]:  %(message)s', '%H:%M:%S')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    host = '127.0.0.1'
    port = 8080
    app.run(host=host, debug=True, threaded=True, port=port)
    logger.info(f'API v1.0 online: http://{host}:{port}')