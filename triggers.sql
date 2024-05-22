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