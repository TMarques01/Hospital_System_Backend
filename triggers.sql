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
    INSERT INTO billing (id, total, data_billing, status, current_payment)
    VALUES ((SELECT COALESCE(MAX(id), 0) + 1 FROM billing), 50, CURRENT_DATE, TRUE, 0);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Remover o trigger existente se existir
DROP TRIGGER IF EXISTS appointment_before_insert ON appointment;

-- Criar trigger para chamar a função create_billing_on_appointment antes de inserir um agendamento
CREATE TRIGGER appointment_before_insert
BEFORE INSERT ON appointment
FOR EACH ROW
EXECUTE FUNCTION create_billing_on_appointment();



-- Função para criar uma entrada na tabela billing ao inserir uma hospitalização
CREATE OR REPLACE FUNCTION create_billing_on_hospitalization() RETURNS TRIGGER AS $$
DECLARE
    new_billing_id INTEGER;
BEGIN
    INSERT INTO billing (id, total, data_billing, status, current_payment) -- cirurgia + hospitalização = 150
    VALUES ((SELECT COALESCE(MAX(id), 0) + 1 FROM billing), 150, CURRENT_DATE, TRUE, 0)
    RETURNING id INTO new_billing_id;
    
    NEW.billing_id := new_billing_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS create_billing_on_hospitalization ON hospitalization;

CREATE TRIGGER create_billing_on_hospitalization
BEFORE INSERT ON hospitalization
FOR EACH ROW
EXECUTE FUNCTION create_billing_on_hospitalization();