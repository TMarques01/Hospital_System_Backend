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
    SELECT 1 FROM surgeries
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


# check if the nurses aare available in the date (Return true if is available and false if is not available)
def are_nurses_available(nurse_ids, date_start, date_end, type):
    if type == 1:
        for nurse_id in nurse_ids:
            query = """ 
            SELECT 1 FROM nurse_role nr
            JOIN surgeries s ON nr.surgeries_id = s.id
            WHERE nr.nurse_contract_employee_person_id = %s
            AND (s.date_start, s.date_end) OVERLAPS (%s, %s)
            UNION ALL
            SELECT 1 FROM nurse_appointment na
            JOIN appointment a ON na.appointment_id = a.id
            WHERE na.nurse_contract_employee_person_id = %s
            AND (a.date_start, a.date_end) OVERLAPS (%s, %s)
            LIMIT 1;
            """
            try:
                with db_connection() as conn:
                    with conn.cursor() as cursor:
                        cursor.execute(query, (nurse_id[0], date_start, date_end, nurse_id[0], date_start, date_end))
                        row = cursor.fetchone()
                        if row is not None:
                            return False
            except (Exception, psycopg2.DatabaseError) as error:
                print(str(error))
                return False
        return True
    else:
        for nurse_id in nurse_ids:
            query = """ 
            SELECT 1 FROM nurse_role nr
            JOIN surgeries s ON nr.surgeries_id = s.id
            WHERE nr.nurse_contract_employee_person_id = %s
            AND (s.date_start, s.date_end) OVERLAPS (%s, %s)
            UNION ALL
            SELECT 1 FROM nurse_appointment na
            JOIN appointment a ON na.appointment_id = a.id
            WHERE na.nurse_contract_employee_person_id = %s
            AND (a.date_start, a.date_end) OVERLAPS (%s, %s)
            LIMIT 1;
            """
            try:
                with db_connection() as conn:
                    with conn.cursor() as cursor:
                        cursor.execute(query, (nurse_id, date_start, date_end, nurse_id, date_start, date_end))
                        row = cursor.fetchone()
                        if row is not None:
                            return False
            except (Exception, psycopg2.DatabaseError) as error:
                print(str(error))
                return False
        return True
        
        
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
                                                                            
                                        # Now you can use appointment_id and billing_id in your INSERT statement
                                        query = """
                                            INSERT INTO appointment 
                                            (id, date_start, date_end, n_room, assistants_contract_employee_person_id, doctor_contract_employee_person_id, pacient_person_id, billing_id) 
                                            VALUES (%s, %s, %s, %s, %s, %s, %s, (SELECT MAX(id) FROM billing));
                                        """
                                        values = (appointment_id, date_start, date_end, n_room, assistant_person_id, doctor_contract_employee_person_id, pacient_person_id,)
                                        
                                        cursor.execute(query, values)
                                        
                                        if "nurse" in payload:
                                            if are_nurses_available(payload["nurse"], date_start, date_end, 0):
                                                nurse_ids = payload["nurse"]
                                                for nurse_id in nurse_ids:
                                                    query_nurse = """
                                                        INSERT INTO nurse_appointment (appointment_id, nurse_contract_employee_person_id)
                                                        VALUES (%s, %s)
                                                    """
                                                    values_nurse = (appointment_id, nurse_id)
                                                    cursor.execute(query_nurse, values_nurse)
                                                    
                                            else:
                                                conn.rollback()
                                                return flask.jsonify({
                                                    "status": StatusCodes['api_error'],
                                                    "error": "Nurse is not available"
                                                })


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


@app.route("/surgery", methods=["POST"])
@app.route("/surgery/<int:hospitalization_id>", methods=["POST"])
def schedule_surgery(hospitalization_id=None):
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
        
        if person_type[1] == "assistant":  # verify if the user is an assistant
            if "pacient_id" in payload and "doctor_id" in payload and "date_start" in payload and "date_end" in payload and "type_surgery" in payload and "nurse" in payload:
                pacient_id = payload["pacient_id"]
                doctor_user_id = payload["doctor_id"]
                date_start = payload["date_start"]
                date_end = payload["date_end"]
                type_surgery = payload["type_surgery"]
                nurses = payload["nurse"]
                
                try:
                    with db_connection() as conn:
                        with conn.cursor() as cursor:
                            if check_date(date_start) and check_date(date_end) and compare_dates(date_start, date_end):
                                if is_doctor_available(doctor_user_id, date_start, date_end):
                                    if are_nurses_available(nurses, date_start, date_end, 1):
                                        
                                        if hospitalization_id is None:  # if don't exist a hospitalization
                                            cursor.execute("SELECT COALESCE(MAX(id), 0) FROM hospitalization;")
                                            hosp_id = cursor.fetchone()[0]
                                            if hosp_id is None:
                                                hosp_id = 0
                                            hosp_id += 1
                                        
                                            # Insert a new record into the hospitalization table
                                            query = """
                                                INSERT INTO hospitalization (id, date_start, date_end, n_bed, assistants_contract_employee_person_id, pacient_person_id, nurse_contract_employee_person_id)
                                                VALUES (%s, %s, %s, (SELECT COALESCE(MAX(n_bed), 0) + 1 FROM hospitalization), %s, %s, %s)
                                                RETURNING id
                                            """
                                            values = (hosp_id, date_start, date_end, person_type[0], pacient_id, nurses[0][0])
                                            cursor.execute(query, values)
                                            hospitalization_id = cursor.fetchone()[0]
                                            
                                            query = """
                                                INSERT INTO surgeries (id, date_start, date_end, n_room, type, doctor_contract_employee_person_id, hospitalization_id)
                                                VALUES ((SELECT COALESCE(MAX(id), 0) + 1 FROM surgeries), %s, %s, (SELECT COALESCE(MAX(n_room),0) + 1 FROM surgeries), %s, %s, %s)
                                                RETURNING id
                                            """
                                            values = (date_start, date_end, type_surgery, doctor_user_id, hospitalization_id)
                                            cursor.execute(query, values)
                                            surgery_id = cursor.fetchone()[0]
                                            conn.commit()

                                            result = {
                                                "hospitalization_id": hospitalization_id,
                                                "surgery_id": surgery_id,
                                                "patient_id": pacient_id,
                                                "doctor_id": doctor_user_id,
                                                "date_start": date_start,
                                                "date_end": date_end,
                                            }
                                            message = {
                                                "status": StatusCodes['success'],
                                                "results": result
                                            }
                                                
                                        else:  # if exist a hospitalization
                                            
                                            cursor.execute("SELECT COALESCE(MAX(id), 0) FROM surgeries;")
                                            surgery_id = cursor.fetchone()[0]
                                            if surgery_id is None:
                                                surgery_id = 0
                                            surgery_id += 1

                                            cursor.execute("SELECT COALESCE(MAX(n_room), 0) FROM surgeries;")
                                            n_room = cursor.fetchone()[0]
                                            if n_room is None:
                                                n_room = 0
                                            n_room += 1

                                            query = """
                                                INSERT INTO surgeries (id, date_start, date_end, n_room, type, doctor_contract_employee_person_id, hospitalization_id)
                                                VALUES (%s, %s, %s, %s, %s, %s, %s)
                                                RETURNING id
                                            """
                                            values = (surgery_id, date_start, date_end, n_room, type_surgery, doctor_user_id, hospitalization_id)
                                            cursor.execute(query, values)
                                            surgery_id = cursor.fetchone()[0]

                                            for nurse in nurses:
                                                query_nurse = """
                                                    INSERT INTO nurse_role (role, surgeries_id, nurse_contract_employee_person_id)
                                                    VALUES (%s, %s, %s)
                                                """
                                                values_nurse = (nurse[1], surgery_id, nurse[0])
                                                cursor.execute(query_nurse, values_nurse)
                                            
                                            conn.commit()

                                            result = {
                                                "hospitalization_id": hospitalization_id,
                                                "surgery_id": surgery_id,
                                                "patient_id": pacient_id,
                                                "doctor_id": doctor_user_id,
                                                "date_start": date_start,
                                                "date_end": date_end,
                                            }
                                            message = {
                                                "status": StatusCodes['success'],
                                                "results": result
                                            }
                                             
                                    else:
                                        message["status"] = StatusCodes['api_error']
                                        message["error"] = "Nurse is not available"
                                else:
                                    message["status"] = StatusCodes['api_error']
                                    message["error"] = "Doctor is not available"
                            else:
                                message["status"] = StatusCodes['api_error']
                                message["error"] = "Wrong parameter in JSON file for appointment!"

                except (Exception, psycopg2.DatabaseError) as error:
                    logger.error(f'POST /surgery - error: {error}')
                    message = {
                        "status": StatusCodes['internal_error'],
                        "errors": str(error)
                    }

                finally:
                    if conn is not None:
                        conn.close()
            else:
                message["status"] = StatusCodes['api_error']
                message["error"] = "Missing parameters"
        else:
            message["status"] = StatusCodes['api_error']
            message["error"] = "You don't have permission to do this action!"
    else:
        message["status"] = StatusCodes['api_error']
        message["error"] = "Token not found!"	
            
    return flask.jsonify(message)


@app.route('/prescriptions/<int:patient_user_id>', methods=['GET'])
def get_prescriptions(patient_user_id):
    logger.info('GET /prescriptions/<patient_user_id>')
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
            person= get_person_type(username)
            
            if person[1]=="nurse" or person[1]=="doctor" or person[1]=="assistant" or (person[1] == "pacient" and person[0] == patient_user_id):
                logger.debug(f'patient_user_id: {person[1]}')
                query = ("""
                    SELECT pr.id, pr.validity, po.dose, po.frequency, m.nome , m.active_principle, se.name, sv.severity, sv.ocurrency
                    FROM prescriptions pr
                    JOIN posology po ON pr.id = po.prescriptions_id
                    JOIN medicine m ON po.medicine_id = m.id
                    LEFT JOIN severity sv ON m.id = sv.medicine_id
                    LEFT JOIN side_effects se ON sv.side_effects_id_effect = se.id_effect
                    LEFT JOIN appointment_prescriptions ap_pr ON pr.id = ap_pr.prescriptions_id
                    LEFT JOIN appointment a ON ap_pr.appointment_id = a.id
                    LEFT JOIN hospitalization_prescriptions hp ON pr.id = hp.prescriptions_id
                    LEFT JOIN hospitalization h ON hp.hospitalization_id = h.id
                    WHERE a.pacient_person_id = %s OR h.pacient_person_id = %s
                """)

                try:
                    cur.execute(query, (patient_user_id,patient_user_id,))
                    rows = cur.fetchall()
                    prescriptions = {}
                    
                    for row in rows:
                        prescription_id = row[0]
                        if prescription_id not in prescriptions:
                            prescriptions[prescription_id] = {
                                'prescription_id': prescription_id,
                                'validity': row[1],
                                'medicines': {}
                            }
                        
                        medicine_name = row[4]
                        if medicine_name not in prescriptions[prescription_id]['medicines']:
                            prescriptions[prescription_id]['medicines'][medicine_name] = {
                                'medicine': medicine_name,
                                'active_principle': row[5],
                                'dose': row[2],
                                'frequency': row[3],
                                'side_effects': []
                            }
                        
                        if row[6]:
                            prescriptions[prescription_id]['medicines'][medicine_name]['side_effects'].append({
                                'name': row[6],
                                'severity': row[7],
                                'ocurrency': row[8]
                            })

                    results = []
                    for prescription in prescriptions.values():
                        prescription_data = {
                            'prescription_id': prescription['prescription_id'],
                            'validity': prescription['validity'],
                            'medicines': []
                        }
                        for medicine in prescription['medicines'].values():
                            prescription_data['medicines'].append(medicine)
                        results.append(prescription_data)
                    
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



@app.route('/prescription', methods=['POST'])
def add_prescription():
    try:
        payload = flask.request.get_json()
    except Exception as e:
        return flask.jsonify({
            "status": StatusCodes['api_error'],
            "error": "No json"
        })

    message = {}

    if "token" in payload:
        try:
            decoded_token = jwt.decode(payload["token"], secret_key, algorithms=['HS256'])
        except Exception as e:
            return flask.jsonify({
                "status": StatusCodes['api_error'],
                "error": "Invalid token"
            })
        
        username = decoded_token["username"]
        person = get_person_type(username)

        if person[1] == "doctor":
            if "type" in payload and "event_id" in payload and "validity" in payload and "medicines" in payload:
                type = payload["type"]
                event_id = payload["event_id"]
                validity = payload["validity"]
                
                try:
                    with db_connection() as conn:
                        with conn.cursor() as cursor:
                            if type in ["appointment", "hospitalization"]:
                                logger.debug(f'POST /prescription - payload: {payload}')
                                
                                cursor.execute("SELECT MAX(id) FROM prescriptions;")
                                prescription_id = cursor.fetchone()[0]
                                if prescription_id is None:
                                    prescription_id = 0
                                prescription_id += 1

                                prescription_query = """INSERT INTO prescriptions (id, validity) VALUES (%s, %s)"""
                                cursor.execute(prescription_query, (prescription_id, validity))

                                if type == "appointment":
                                    query = """INSERT INTO appointment_prescriptions (appointment_id, prescriptions_id) VALUES (%s, %s)"""
                                    cursor.execute(query, (event_id,prescription_id))
                                    
                                elif type == "hospitalization":
                                    query = """INSERT INTO hospitalization_prescriptions (hospitalization_id, prescriptions_id) VALUES (%s, %s)"""
                                    cursor.execute(query, (event_id, prescription_id))
                                    
                                if "medicines" in payload:
                                    medicines = payload["medicines"]
                                    for medicine in medicines:
                                        if "medicine" in medicine and "dose" in medicine and "frequency" in medicine:
                                            medicine_name = medicine["medicine"]
                                            dose = medicine["dose"]
                                            frequency = medicine["frequency"]
                                            posology_query = """
                                            INSERT INTO posology (dose, frequency, medicine_id, prescriptions_id)
                                            VALUES (%s, %s, (SELECT id FROM medicine WHERE nome = %s), %s)"""
                                            posology_values = (dose, frequency, medicine_name, prescription_id)
                                            cursor.execute(posology_query, posology_values)
                                        else:
                                            raise ValueError("Incomplete medicine information in payload")

                                conn.commit()
                                message['status'] = StatusCodes['success']
                                message['message'] = "Prescription created"
                                message['prescription_id'] = prescription_id
                            else:
                                message['status'] = StatusCodes['api_error']
                                message['message'] = "Type not valid"

                except (Exception, psycopg2.DatabaseError) as error:
                    logger.error(f'POST /prescription - error: {error}')
                    message = {
                        "status": StatusCodes['internal_error'],
                        "error": str(error)
                    }
                    conn.rollback()
            else:
                message["status"] = StatusCodes['api_error']
                message["error"] = "Wrong parameter in JSON file for prescription!"
        else:
            message["status"] = StatusCodes['api_error']
            message["error"] = "You don't have permission to do this action!"
    else:
        message["status"] = StatusCodes['api_error']
        message["error"] = "Token not found!"

    return flask.jsonify(message)




@app.route("/bills/<int:bill_id>", methods=["POST"])
def bill_payment(bill_id):
    
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
        
        if person_type[1] == "pacient":  # verify if the user is an assistant
            if "amount" in payload and "payment_method" in payload:
                amount = payload["amount"]
                method = payload["payment_method"]
                try:
                    with db_connection() as conn:
                        with conn.cursor() as cursor:
                            if is_digit(amount) and is_digit(bill_id):
                                # Check if the billing is already paid
                                query = """
                                    SELECT status
                                    FROM billing
                                    WHERE id = %s
                                """
                                values = (bill_id,)
                                cursor.execute(query, values)
                                billing_status = cursor.fetchone()[0]

                                if billing_status is True: # if billing is not payed
                                    if method in ["cash", "credit_card", "debit_card"]:
                                        
										# Get the total amount of the billing
                                        query = """
											SELECT total
											FROM billing
											WHERE id = %s
										"""
                                        values = (bill_id,)
                                        cursor.execute(query, values)
                                        billing_total = cursor.fetchone()[0]

                                        if billing_total is not None:

                                            # Check the total amount of payments for the given billing_id
                                            query = """
												SELECT COALESCE(SUM(amount), 0)
												FROM payment
												WHERE billing_id = %s
											"""
           
                                            values = (bill_id,)
                                            cursor.execute(query, values)
                                            payments_total = cursor.fetchone()[0]

                                            if payments_total + amount < billing_total:

												# Create a new payment
                                                query = """
													INSERT INTO payment (id, amount, data, type, billing_id)
													VALUES ((SELECT COALESCE(MAX(id), 0) + 1), %s, CURRENT_DATE, %s, %s)
												"""
                                                values = (amount, method, bill_id)
                                                cursor.execute(query, values)
                                                
                                                # update de current value of the billing
                                                query_update_billing = """
                                                    UPDATE billing
                                                    SET current_payment = %s
                                                    WHERE id = %s
                                                """
                                
                                                values = (amount, bill_id,)
                                                cursor.execute(query_update_billing, values)
                                                conn.commit()

                                                # Check if there are any more unpaid amounts for the given billing_id
                                                remaining_amount = billing_total - payments_total - amount

                                                if remaining_amount == 0:
                                                    # Update the billing status to paid
                                                    query = """
                                                        UPDATE billing
                                                        SET status = True
                                                        WHERE id = %s
                                                    """
                                                    values = (bill_id,)
                                                    cursor.execute(query, values)

                                                conn.commit()


                                                if remaining_amount > 0:
                                                    message = {
                                                        "status": StatusCodes['success'],
                                                        "results": f"Payment done with success. There is still an unpaid amount of {remaining_amount}."
                                                    }
                                                else:
                                                    
                                                    message = {
                                                        "status": StatusCodes['success'],
                                                        "results": "Payment done with success. The total billing has been paid."
                                                    }
                                            else:
                                                message["status"] = StatusCodes['api_error']
                                                message["error"] = f"The amount exceeds the total billing. The amount left is: {billing_total - payments_total}."
                                            
                                        else:
                                            message["status"] = StatusCodes['api_error']
                                            message["error"] = "No billing found with this id"
                                    else:
                                        message["status"] = StatusCodes['api_error']
                                        message["error"] = "Wrong payment method"
                                else:
                                    message["status"] = StatusCodes['api_error']
                                    message["error"] = "The billing is already paid"
                            else:
                                message["status"] = StatusCodes['api_error']
                                message["error"] = "Wrong amount (not an Integer)"  
                
                except (Exception, psycopg2.DatabaseError) as error:
                    logger.error(f'POST /surgery - error: {error}')
                    message = {
                        "status": StatusCodes['internal_error'],
                        "errors": str(error)
                    }

                finally:
                    if conn is not None:
                        conn.close()
            else:
                message["status"] = StatusCodes['api_error']
                message["error"] = "Missing parameters"
        else:
            message["status"] = StatusCodes['api_error']
            message["error"] = "You don't have permission to do this action!"
    else:
        message["status"] = StatusCodes['api_error']
        message["error"] = "Token not found!"	
            
    return flask.jsonify(message)


@app.route("/top3patients", methods=["GET"])
def get_top3_patients():
    try:
        payload = flask.request.get_json()
    except:
        return flask.jsonify({
            "status": StatusCodes['api_error'],
            "error": "No json"
        })

    if "token" in payload:
        decoded_token = jwt.decode(payload["token"], secret_key, algorithms=['HS256'])
        username = decoded_token["username"]
        person_type = get_person_type(username)

        if person_type[1] == "assistant":  # verify if the user is an assistant
            try:
                with db_connection() as conn:
                    with conn.cursor() as cursor:
                        # Get the top 3 patients who spent the most
                        query = """
                            WITH patient_payments AS (
                                SELECT hospitalization.pacient_person_id AS patient_id, SUM(billing.total) AS total_amount
                                FROM hospitalization
                                JOIN billing ON hospitalization.billing_id = billing.id
                                GROUP BY hospitalization.pacient_person_id
                                UNION ALL
                                SELECT appointment.pacient_person_id AS patient_id, SUM(billing.total) AS total_amount
                                FROM appointment
                                JOIN billing ON appointment.billing_id = billing.id
                                GROUP BY appointment.pacient_person_id
                            ),
                            patient_procedures AS (
                                SELECT hospitalization.pacient_person_id AS patient_id, 
                                       ARRAY_AGG(json_build_object('id', surgeries.id, 'doctor_id', surgeries.doctor_contract_employee_person_id, 'date', surgeries.date_start)) AS procedures
                                FROM surgeries
                                JOIN hospitalization ON surgeries.hospitalization_id = hospitalization.id
                                GROUP BY hospitalization.pacient_person_id
                                UNION ALL
                                SELECT appointment.pacient_person_id AS patient_id, 
                                       ARRAY_AGG(json_build_object('id', appointment.id, 'doctor_id', appointment.doctor_contract_employee_person_id, 'date', appointment.date_start)) AS procedures
                                FROM appointment
                                GROUP BY appointment.pacient_person_id
                            )
                            SELECT person.nome AS patient_name, SUM(patient_payments.total_amount) AS amount_spent, MAX(patient_procedures.procedures) AS procedures
                            FROM patient_payments
                            JOIN patient_procedures ON patient_payments.patient_id = patient_procedures.patient_id
                            JOIN person ON patient_payments.patient_id = person.id
                            GROUP BY person.nome
                            ORDER BY amount_spent DESC
                            LIMIT 3;
                        """
                        cursor.execute(query)
                        top3_patients = cursor.fetchall()

                        # Format the results
                        formatted_results = [{
                            "patient_name": row[0],
                            "amount_spent": row[1],
                            "procedures": row[2]
                        } for row in top3_patients]

                        return flask.jsonify({
                            "status": StatusCodes['success'],
                            "results": formatted_results
                        })

            except Exception as e:
                return flask.jsonify({
                    "status": StatusCodes['api_error'],
                    "error": str(e)
                })
        else:
            return flask.jsonify({
                "status": StatusCodes['api_error'],
                "error": "Only assistants can use this endpoint."
            })
    else:
        return flask.jsonify({
            "status": StatusCodes['api_error'],
            "error": "No token provided."
        })

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
    
    
    
    
