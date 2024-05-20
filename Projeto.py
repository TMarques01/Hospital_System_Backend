import flask
import logging
import psycopg2
import datetime
import calendar
import time
import jwt
import random
import hashlib 

app = flask.Flask(__name__)

StatusCodes = {
    'success': 200,
    'api_error': 400,
    'internal_error': 500
}


# ====================================
# DB acess
# ====================================
def db_connection():
    db = psycopg2.connect(
        user='aulaspl',
        password='aulaspl',
        host='localhost',
        port='5432',
        database='projeto'
    )

    return db


# ====================================
# DATA Verification and AUX Functions
# ====================================
def check_contacto(numero):
    try:
        numero = str(numero)  
        numero = numero.replace(" ", "")
        return len(numero) == 9 and numero.isdigit() and numero[0] != '0'
    except:
        return False



# get the max id and increment 1
def get_id(cursor, person_type):

    if person_type == "person": # get the id for the "person" table
        id_query = "SELECT MAX(id) AS max_id FROM person"
        cursor.execute(id_query)
        max_id = cursor.fetchone()[0]
        if max_id is None:
            id = 0
        else:
            id = max_id + 1
    else: # get the id for the "contract" table
        id_query = "SELECT MAX(id) AS max_id FROM contract_employee"
        cursor.execute(id_query)
        max_id = cursor.fetchone()[0]
        if max_id is None:
            id = 0
        else:
            id = max_id + 1

    return id



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



# End Points
@app.route("/register/<person_type>", methods=["POST"])
def register(person_type):

    try:
        payload = flask.request.get_json()
    except:
        return flask.jsonify({
            "status": StatusCodes['api_error'],
            "error": "No json"
        })
    
    message = {}

    if person_type in ["patient", "doctor", "assistant", "nurse"]:

        logger.debug(f'person_type: {person_type}')
        logger.info(f'POST /register/{person_type}')

        if "nome" in payload and "contact" in payload and "email" in payload and "address" in payload and "password" in payload and "username" in payload:

            nome = payload["nome"]
            contact = payload["contact"]
            email = payload["email"]
            address = payload["address"]
            password = hashlib.sha256(payload["password"].encode()).hexdigest() # encode the message
            username = payload["username"]

            get_contact = "SELECT contact FROM person WHERE contact = %s"
            values_contact = (contact,)
            get_email =  "SELECT email FROM person WHERE email = %s"
            values_email = (email,)
            get_username = "SELECT username FROM person WHERE username = %s"
            values_username = (username,)

            try:
                with db_connection() as conn:
                    with conn.cursor() as cursor:
                        if check_contacto(contact): # verify if the contact is with the correct format
                            cursor.execute(get_contact, values_contact)
                            if cursor.rowcount == 0: # contact is already used
                                cursor.execute(get_email, values_email)
                                if cursor.rowcount == 0: # email is already used
                                    cursor.execute(get_username, values_username)
                                    if cursor.rowcount == 0: # username is already used
                                        id = get_id(cursor, "person")
                                        if person_type == "patient": # if is patient
                                            if "historic" in payload:

                                                logger.debug(f'POST /projeto/register/patient - payload: {payload}')
                                                historic = payload["historic"]

                                                query_main = "INSERT INTO person (id, nome, contact, address, email, password, username) VALUES (%s, %s, %s, %s, %s, %s, %s)"
                                                values_query = (id, nome, contact, address, email, password, username,)
                                                cursor.execute(query_main, values_query)

                                                query_pacient = "INSERT INTO pacient (historic, person_id) VALUES (%s, %s)"
                                                values_pacient = (historic, id,)
                                                cursor.execute(query_pacient, values_pacient)

                                                conn.commit()

                                                message['status'] = StatusCodes['success']
                                                message['results'] = id
                                                message['message'] = "Registration Completed"

                                            else:
                                                message["status"] = StatusCodes['api_error']
                                                message["error"] = "Wrong parameter: Historic"   
                                        else: # if is an employee

                                            if "data" in payload and "duration" in payload: # check if have the contract information
                                                data = payload["data"]
                                                duration = payload["duration"]
                                                contract_id = get_id(cursor, "employee")
                                                logger.debug(f'Generated person id: {id}')
                                                # start checking if have the specific information about the role
                                                if person_type == "assistant": # inserting for assistant
                                                    if "license" in payload:
                                                        logger.debug(f'POST /projeto/register/assistant - payload: {payload}')
                                                        license = payload["license"]

                                                        query_main = "INSERT INTO person (id, nome, contact, address, email, password, username) VALUES (%s, %s, %s, %s, %s, %s, %s)"
                                                        values_query = (id, nome, contact, address, email, password, username,)
                                                        cursor.execute(query_main, values_query)    

                                                        query_contract = "INSERT INTO contract_employee (id, data, duration, person_id) VALUES (%s, %s, %s, %s)"
                                                        values_contract = (contract_id, data, duration, id,)
                                                        cursor.execute(query_contract, values_contract)

                                                        query_assistant = "INSERT INTO assistants (license, contract_employee_person_id) VALUES (%s, %s)"
                                                        values_assistant = (license, id,)
                                                        cursor.execute(query_assistant, values_assistant)

                                                        conn.commit()

                                                        message['status'] = StatusCodes['success']
                                                        message['results'] = id
                                                        message['message'] = "Registration Completed"
                                                        
                                                    else:
                                                        message["status"] = StatusCodes['api_error']
                                                        message["error"] = "Wrong parameter in license for assistant" 

                                                elif person_type == "nurse":
                                                    if "category" in payload: # inserting for nurses
                                                        logger.debug(f'POST /projeto/register/nurse - payload: {payload}')
                                                        category = payload["category"]

                                                        query_main = "INSERT INTO person (id, nome, contact, address, email, password, username) VALUES (%s, %s, %s, %s, %s, %s, %s)"
                                                        values_query = (id, nome, contact, address, email, password, username,)
                                                        cursor.execute(query_main, values_query)    

                                                        query_contract = "INSERT INTO contract_employee (id, data, duration, person_id) VALUES (%s, %s, %s, %s)"
                                                        values_contract = (contract_id, data, duration, id,)
                                                        cursor.execute(query_contract, values_contract)

                                                        query_nurse = "INSERT INTO nurse (category, contract_employee_person_id) VALUES (%s, %s)"
                                                        values_nurse = (category, id)
                                                        cursor.execute(query_nurse, values_nurse)

                                                        conn.commit()

                                                        message['status'] = StatusCodes['success']
                                                        message['results'] = id
                                                        message['message'] = "Registration Completed"

                                                    else:
                                                        message["status"] = StatusCodes['api_error']
                                                        message["error"] = "Wrong parameter in category for nurse" 
                                                else:
                                                    if "medical_license" in payload: # insertin for doctors
                                                        logger.debug(f'POST /projeto/register/doctor - payload: {payload}')
                                                        medical_license = payload["medical_license"]

                                                        query_main = "INSERT INTO person (id, nome, contact, address, email, password, username) VALUES (%s, %s, %s, %s, %s, %s, %s)"
                                                        values_query = (id, nome, contact, address, email, password, username,)
                                                        cursor.execute(query_main, values_query)    

                                                        query_contract = "INSERT INTO contract_employee (id, data, duration, person_id) VALUES (%s, %s, %s, %s)"
                                                        values_contract = (contract_id, data, duration, id,)
                                                        cursor.execute(query_contract, values_contract)

                                                        query_doctor = "INSERT INTO doctor (medical_license, contract_employee_person_id) VALUES (%s, %s)"
                                                        values_doctor = (medical_license, id)
                                                        cursor.execute(query_doctor, values_doctor)  

                                                        conn.commit()

                                                        message['status'] = StatusCodes['success']
                                                        message['results'] = id
                                                        message['message'] = "Registration Completed"                                          

                                                    else:
                                                        message["status"] = StatusCodes['api_error']
                                                        message["error"] = "Wrong parameter in category for nurse" 
                                            else:
                                                message["status"] = StatusCodes['api_error']
                                                message["error"] = "Wrong parameter in Contract" 
                                    else:
                                        message["status"] = StatusCodes['api_error']
                                        message["error"] = "username already exists!"                                    
                                else:
                                    message["status"] = StatusCodes['api_error']
                                    message["error"] = "email already exists!"
                            else:
                                message["status"] = StatusCodes['api_error']
                                message["error"] = "contact already exists!"
                        else:
                            message["status"] = StatusCodes['api_error']
                            message["error"] = "Contact with wrong format!"
            except (Exception, psycopg2.DatabaseError) as error:
                logger.error(f'POST /register/pacient - error: {error}')
                message = {
                    "status": StatusCodes['internal_error'],
                    "error": str(error)
                    }
        
                # an error occurred, rollback
                conn.rollback()

            finally:
                if conn is not None:
                    conn.close()
        else:
            message["status"] = StatusCodes['api_error']
            message["error"] = "Wrong parameter in JSON file for person!"   
    else:
        message["status"] = StatusCodes['api_error']
        message["error"] = "Wrong parameter in End Point!"

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