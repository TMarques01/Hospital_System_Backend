INSERT INTO billing 
(id, total, data_billing) 
VALUES (0, 0, '1111-11-11')0

-- Appointment billing trigger

CREATE OR REPLACE FUNCTION create_billing_on_appointment()
RETURNS TRIGGER AS $$
DECLARE
    new_billing_id INTEGER;
BEGIN
    INSERT INTO billing (id, total, data_billing)
    VALUES ((SELECT COALESCE(MAX(id), 0) + 1 FROM billing), 50, CURRENT_DATE)
    RETURNING id INTO new_billing_id;

    UPDATE appointment SET billing_id = new_billing_id WHERE id = NEW.id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS appointment_after_insert ON appointment;

CREATE TRIGGER appointment_after_insert
AFTER INSERT ON appointment
FOR EACH ROW
EXECUTE FUNCTION create_billing_on_appointment();

-- Easy to visualize the data

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
ORDER BY id;
