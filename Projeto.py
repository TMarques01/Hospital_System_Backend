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
        user='postgres',
        password='postgres',
        host='localhost',
        port='5432',
        database='projeto'
    )

    return db


def check_contacto(numero):
    try:
        numero = str(numero)  
        numero = numero.replace(" ", "")
        return len(numero) == 9 and numero.isdigit() and numero[0] != '0'
    except:
        return False

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

@app.route("/register/patient/", methods=["POST"])
def register_patient():
    logger.info('POST /register/patient')

    try:
        payload = request.get_json()
    except:
        return jsonify({
            "status": StatusCodes['api_error'],
            "error": "No json"
        })

    message = {}

    if "nome" in payload and "contact" in payload and "email" in payload and "address" in payload and "password" in payload and "username" in payload and "historic" in payload:
        logger.debug(f'POST /projeto/register/patient - payload: {payload}')

        nome = payload["nome"]
        contact = payload["contact"]
        email = payload["email"]
        address = payload["address"]
        password = hashlib.sha256(payload["password"].enconde()).hexdigest() # encode the message
        username = payload["username"]
        historic = payload["historic"]

        get_contact = "SELECT contact FROM person WHERE contact = %d"
        values_contact = (contact,)
        get_email =  "SELECT email FROM person WHERE email like %s"
        values_email = (email,)
        get_username = "SELECT username FROM person WHERE username like %s"
        values_username = (username,)

        try:
            with db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(get_contact, values_contact)
                    if cursor.rowcount == 0:
                        cursor.execute(get_email, values_email)
                        if cursor.rowcount == 0:
                            cursor.execute(get_username, values_username)
                            if cursor.rowcount == 0:

                                # get the max id to increment 1
                                id_query = "SELECT MAX(id) AS max_id FROM person"
                                cursor.execute(id_query)
                                max_id = cursor.fetchone()[0]
                                if max_id is None:
                                    id = 0
                                else:
                                    id = max_id + 1

                                query_principal = "INSERT INTO person (id, nome, contact, address, email, password, username) VALUES (%d, %s, %d, %s, %s, %s, %s)"
                                values_query = (id, nome, contact, address, email, password, username,)
                                cursor.execute(query_principal, values_query)

                                query_pacient = "INSERT INTO pacient (historic, person_id) VALUES (%s, %d)"
                                values_pacient = (historic, id,)
                                cursor.execute(query_pacient, values_pacient)

                                conn.commit()

                                message['status'] = StatusCodes['success']
                                message['results'] = id
                                message['message'] = "Registration Completed"

                            else:
                                message["status"] = StatusCodes['api_error']
                                message["error"] = "username already exists!"                                    

                        else:
                            message["status"] = StatusCodes['api_error']
                            message["error"] = "email already exists!"
                    else :
                        message["status"] = StatusCodes['api_error']
                        message["error"] = "contact already exists!"
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

    return flask.jsonify(message)




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