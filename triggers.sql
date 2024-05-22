INSERT INTO billing 
(id, total, data_billing) 
VALUES (0, 0, '1111-11-11')



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

DROP TRIGGER IF EXISTS surgery_before_insert ON surgery;

CREATE TRIGGER surgery_before_insert
BEFORE INSERT ON surgery
FOR EACH ROW
EXECUTE FUNCTION create_hospitalization_on_surgery();
