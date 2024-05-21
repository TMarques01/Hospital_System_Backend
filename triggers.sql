INSERT INTO billing 
(id, total, data_billing) 
VALUES (0, 0, '1111-11-11')

--________________________________________________________________________________________

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
