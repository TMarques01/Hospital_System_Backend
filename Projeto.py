import flask
import logging
import psycopg2
import datetime
import calendar
import time
import jwt
import random
import hashlib 
from datetime import datetime


secret_key = 'VamosTerBoaNota'

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

# verify if the contact is with the correct format
def check_contacto(numero):
    try:
        numero = str(numero)  
        numero = numero.replace(" ", "")
        return len(numero) == 9 and numero.isdigit() and numero[0] != '0'
    except:
        return False
    

# check if the date is in the correct format
def check_date(date, format="%Y-%m-%d %H:%M:%S"):

    try:
        datetime.strptime(date, format)
        return True
    except ValueError:
        return False


# compare two dates if d1 is before d2
def compare_dates(date1, date2, format="%Y-%m-%d %H:%M:%S"):
    try:
        d1 = datetime.strptime(date1, format)
        d2 = datetime.strptime(date2, format)
        return date1 if d1 < d2 else date2
    except ValueError:
        return None


# check if the value is a digit
def is_digit(n):
    try:
        int(n)
        return True
    except ValueError:
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


# get the person type based on the username
def get_person_type(username):
    query = """
    SELECT person.id, person.username, 
    CASE 
        WHEN assistants.contract_employee_person_id IS NOT NULL THEN 'assistant'
        WHEN doctor.contract_employee_person_id IS NOT NULL THEN 'doctor'
        WHEN nurse.contract_employee_person_id IS NOT NULL THEN 'nurse'	
        ELSE 'pacient'
    END as specification
    FROM person
    LEFT JOIN assistants ON person.id = assistants.contract_employee_person_id
    LEFT JOIN doctor ON person.id = doctor.contract_employee_person_id
    LEFT JOIN nurse ON person.id = nurse.contract_employee_person_id
    WHERE person.username = %s;
    """
    try:
        with db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (username,))
                row = cursor.fetchone()
                if row is None:
                    response = {'status': StatusCodes['api_error'], 'error': 'User not found'}
                else:     
                    # specification = [id, specification] 
                    specification = []
                    specification.append(row[0])
                    specification.append(row[2])

    except Exception as e:
        response = {'status': StatusCodes['api_error'], 'error': str(e)}
    return specification


# check if the doctor is available in the date (Return true if is available and false if is not available)
def is_doctor_available(doctor_id, date_start, date_end):
    query = """ 
    SELECT 1 FROM surgeries_nurse_role
    WHERE doctor_contract_employee_person_id = %s
    AND (date_start, date_end) OVERLAPS (%s, %s)
    UNION ALL
    SELECT 1 FROM appointment
    WHERE doctor_contract_employee_person_id = %s
    AND (date_start, date_end) OVERLAPS (%s, %s)
    LIMIT 1;
    """
    try:
        with db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (doctor_id, date_start, date_end, doctor_id, date_start, date_end))
                row = cursor.fetchone()
                return row is None
    except (Exception, psycopg2.DatabaseError) as error:
        print(str(error))
        return False


# check if the room is available in the date (Return true if is available and false if is not available)
def is_room_avaliable(cursor, n_room, date_start, date_end):
    query_check_room = """
        SELECT COUNT(*)
        FROM appointment
        WHERE n_room = %s AND
        (date_start < %s AND date_end > %s OR
        date_start < %s AND date_end > %s OR
        date_start >= %s AND date_end <= %s)
    """
    values_check_room = (n_room, date_end, date_start, date_start, date_end, date_start, date_end)

    cursor.execute(query_check_room, values_check_room)
    room_count = cursor.fetchone()[0]

    if room_count == 0:
        return True
    else:
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

# ====================================
# End Points
# ====================================
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

        if "nome" in payload and "contact" in payload and "email" in payload and "address" in payload and "password" in payload and "username" in payload :

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


@app.route("/user", methods=["PUT"])
def login():
    try:
        payload = flask.request.get_json()
    except:
        return flask.jsonify({
            "status": StatusCodes['internal_error'],
            "error": "No JSON"
        })

    if "username" not in payload or "password" not in payload:
        return flask.appcontext_pushedjsonify({
            "code": StatusCodes['api_error'],
            "message": "Wrong parameters"
        })

    logger.info(f'PUT /user')
    nome_utilizador = payload["username"]
    password = hashlib.sha256(payload["password"].encode()).hexdigest()
    query = "SELECT password FROM person WHERE username = %s"
    message = {}

    try:
        with db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (nome_utilizador,))

                if cursor.rowcount == 0:
                    message["status"] = StatusCodes['api_error']
                    message["error"] = f"No user with that credentials: {nome_utilizador}"
                else:
                    row = cursor.fetchone()
                    if password == row[0]:
                        # get the token
                        username = {'username': nome_utilizador}
                        token = jwt.encode(username, secret_key, algorithm='HS256')
                        message["status"] = StatusCodes['success']
                        message["token"] = token
                    else:
                        message["status"] = StatusCodes['api_error']
                        message["error"] = "Wrong Password"
                        
    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f'PUT /user - error: {error}')
        return flask.jsonify({
            "status": StatusCodes['internal_error'],
            "error": str(error)
        })
    

    finally:
        if conn is not None:
            conn.close()

    return flask.jsonify(message)
    

@app.route("/appointment", methods=["POST"])
def create_appointment():
    try:
        payload = flask.request.get_json()
    except:
        return flask.jsonify({
            "status": StatusCodes['api_error'],
            "error": "No json"
        })
    
    message = {}

    if "token" in payload:
        decoded_token = jwt.decode(payload["token"], secret_key, algorithms=['HS256'])
        username = decoded_token["username"]
        person_type = get_person_type(username)
        if person_type[1] == "assistant": # verify if the user is an assistant
    
            if "date_start" in payload and "date_end" in payload and "n_room" in payload and  "doctor" in payload and "pacient" in payload:

                date_start = payload["date_start"]
                date_end = payload["date_end"]
                n_room = payload["n_room"]
                doctor_contract_employee_person_id = payload["doctor"]
                pacient_person_id = payload["pacient"]
                assistant_person_id = person_type[0]

                try:
                    with db_connection() as conn:
                        with conn.cursor() as cursor:
                            if check_date(date_start) and check_date(date_end) and is_digit(n_room) and compare_dates(date_start, date_end):
                                if is_doctor_available(doctor_contract_employee_person_id, date_start, date_end):
                                    if is_room_avaliable(cursor, n_room, date_start, date_end):

                                        logger.debug(f'POST /appointment - payload: {payload}')

                                        # Get the current maximum appointment ID
                                        cursor.execute("SELECT MAX(id) FROM appointment;")
                                        appointment_id = cursor.fetchone()[0]
                                        if appointment_id is None:
                                            appointment_id = 0
                                        
                                        appointment_id += 1
                                        billing_id = 0 # using the default billing_id
                                        
                                        # Now you can use appointment_id and billing_id in your INSERT statement
                                        query = """
                                            INSERT INTO appointment 
                                            (id, date_start, date_end, n_room, assistants_contract_employee_person_id, doctor_contract_employee_person_id, pacient_person_id, billing_id) 
                                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                                        """
                                        values = (appointment_id, date_start, date_end, n_room, assistant_person_id, doctor_contract_employee_person_id, pacient_person_id, billing_id)
                                        
                                        cursor.execute(query, values)

                                        conn.commit()
                    
                                        message['status'] = StatusCodes['success']
                                        message['message'] = "Appointment created"
                                        message['appointment_id'] = appointment_id
                                    else:
                                        # The room is not available, return an error message
                                        message['status'] = StatusCodes['api_error']
                                        message['message'] = "Room is not available"
                                else:
									# The room is not available, return an error message
                                    message['status'] = StatusCodes['api_error']
                                    message['message'] = "Doctor is not available"
                            else:
								# The room is not available, return an error message
                                message['status'] = StatusCodes['api_error']
                                message['message'] = "Data or Room not valid"

                except (Exception, psycopg2.DatabaseError) as error:
                    logger.error(f'POST /appointment - error: {error}')
                    message = {
                        "status": StatusCodes['internal_error'],
                        "error": str(error)
                    }
                    conn.rollback()

                finally:
                    if conn is not None:
                        conn.close()
            else:
                message["status"] = StatusCodes['api_error']
                message["error"] = "Wrong parameter in JSON file for appointment!"
        else:
            message["status"] = StatusCodes['api_error']
            message["error"] = "You don't have permission to do this action!"
    else:
        message["status"] = StatusCodes['api_error']
        message["error"] = "Token not found!"

    return flask.jsonify(message)


@app.route('/appointments/<int:patient_user_id>', methods=['GET'])
def see_appointment(patient_user_id):
    logger.info('GET /appointament/<patient_user_id>')
    logger.debug(f'patient_user_id: {patient_user_id}')
    
    try:
        payload = flask.request.get_json()
    except:
        return flask.jsonify({
            "status": StatusCodes['api_error'],
            "error": "No json"
        })
 
    message = {}
    
    try:
        conn = db_connection()
        cur = conn.cursor()
    
        if "token" in payload:
            decoded_token = jwt.decode(payload["token"], secret_key, algorithms=['HS256'])
            username = decoded_token["username"]
            person_type = get_person_type(username)
            
            if person_type[1] == "assistant" or (person_type[1] == "pacient" and person_type[0] == patient_user_id):
                
                query =("""SELECT a.id, a.date_start, a.date_end, a.n_room, dp.nome AS doctor_name
               			FROM appointment a
                		JOIN doctor doc ON a.doctor_contract_employee_person_id = doc.contract_employee_person_id
                		JOIN person dp ON doc.contract_employee_person_id = dp.id
               			WHERE a.pacient_person_id = %s""")
                
                try:
                    cur.execute(query, (patient_user_id,))
                    rows = cur.fetchall()
                    results = []
                    
                    for row in rows:
                        appointment = {'id_appointment': row[0], 'date_start': row[1], 'date_end': row[2], 'room': row[3], 'doctor_name': row[4]}
                        results.append(appointment)
                        logger.debug(row)

                    message = {'status': StatusCodes['success'], 'results': results}

                except (Exception, psycopg2.DatabaseError) as error:
                    message = {
                        "status": StatusCodes['internal_error'],
                        "error": str(error)
                    }
                    conn.rollback()

            else:
                message["status"] = StatusCodes['api_error']
                message["error"] = "You don't have permission to do this action!"
        else:
            message["status"] = StatusCodes['api_error']
            message["error"] = "Token not found!"
    
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
    
    
    
    


