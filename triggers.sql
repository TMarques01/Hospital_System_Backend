-- Selecionar dados da tabela person e realizar joins
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

-- Função para criar uma entrada na tabela billing ao inserir um agendamento
CREATE OR REPLACE FUNCTION create_billing_on_appointment() RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO billing (id, total, data_billing)
    VALUES ((SELECT COALESCE(MAX(id), 0) + 1 FROM billing), 50, NOW());
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS appointment_before_insert ON appointment;

CREATE TRIGGER appointment_before_insert
BEFORE INSERT ON appointment
FOR EACH ROW
EXECUTE FUNCTION create_billing_on_appointment();

-- Função para criar uma entrada na tabela billing ao inserir uma hospitalização
CREATE OR REPLACE FUNCTION create_billing_on_hospitalization() RETURNS TRIGGER AS $$
DECLARE
    new_billing_id INTEGER;
BEGIN
    INSERT INTO billing (id, total, data_billing)
    VALUES ((SELECT COALESCE(MAX(id), 0) + 1 FROM billing), 100, NOW())
    RETURNING id INTO new_billing_id;
    
    NEW.billing_id := new_billing_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Função para criar uma entrada na tabela hospitalization ao inserir uma cirurgia
CREATE OR REPLACE FUNCTION create_hospitalization_on_surgery() RETURNS TRIGGER AS $$
DECLARE
    new_hosp_id INTEGER;
BEGIN
    INSERT INTO hospitalization (date_start, date_end, n_bed, assistants_contract_employee_person_id, pacient_person_id, nurse_contract_employee_person_id)
    VALUES (NEW.date_surgery, NEW.date_surgery + INTERVAL '1 day', (SELECT COALESCE(MAX(n_bed), 0) + 1 FROM hospitalization), NEW.assistant_id, NEW.pacient_id, NEW.nurse_id)
    RETURNING id INTO new_hosp_id;
    
    NEW.hospitalization_id := new_hosp_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS surgery_before_insert ON surgeries;

CREATE TRIGGER surgery_before_insert
BEFORE INSERT ON surgeries
FOR EACH ROW
EXECUTE FUNCTION create_hospitalization_on_surgery();
