CREATE OR REPLACE FUNCTION create_billing_on_appointment()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO billing (id, total, data_billing)
    VALUES ((SELECT COALESCE(MAX(id), 0) + 1 FROM billing), NEW.total, CURRENT_DATE);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS appointment_after_insert ON appointment;

CREATE TRIGGER appointment_after_insert
AFTER INSERT ON appointment
FOR EACH ROW
EXECUTE FUNCTION create_billing_on_appointment();