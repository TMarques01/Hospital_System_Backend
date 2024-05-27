CREATE TABLE pacient (
	historic	 TEXT,
	person_id BIGINT,
	PRIMARY KEY(person_id)
);

CREATE TABLE doctor (
	medical_license		 TEXT NOT NULL,
	contract_employee_person_id BIGINT,
	PRIMARY KEY(contract_employee_person_id)
);

CREATE TABLE nurse (
	category			 VARCHAR(512),
	contract_employee_person_id BIGINT,
	PRIMARY KEY(contract_employee_person_id)
);

CREATE TABLE assistants (
	license			 BIGINT NOT NULL,
	contract_employee_person_id BIGINT,
	PRIMARY KEY(contract_employee_person_id)
);

CREATE TABLE surgeries (
	id				 BIGINT,
	date_start			 TIMESTAMP NOT NULL,
	date_end				 TIMESTAMP,
	n_room				 BIGINT NOT NULL,
	type				 VARCHAR(512),
	doctor_contract_employee_person_id BIGINT NOT NULL,
	hospitalization_id		 BIGINT NOT NULL,
	PRIMARY KEY(id)
);

CREATE TABLE hospitalization (
	id					 BIGINT,
	date_start				 TIMESTAMP NOT NULL,
	date_end				 TIMESTAMP,
	n_bed					 BIGINT NOT NULL,
	assistants_contract_employee_person_id BIGINT NOT NULL,
	billing_id				 BIGINT NOT NULL,
	pacient_person_id			 BIGINT NOT NULL,
	nurse_contract_employee_person_id	 BIGINT NOT NULL,
	PRIMARY KEY(id)
);

CREATE TABLE appointment (
	id					 BIGINT,
	date_start				 TIMESTAMP NOT NULL,
	date_end				 TIMESTAMP NOT NULL,
	n_room				 BIGINT NOT NULL,
	assistants_contract_employee_person_id BIGINT NOT NULL,
	billing_id				 BIGINT NOT NULL,
	doctor_contract_employee_person_id	 BIGINT NOT NULL,
	pacient_person_id			 BIGINT NOT NULL,
	PRIMARY KEY(id)
);

CREATE TABLE prescriptions (
	id	 BIGINT,
	validity DATE NOT NULL,
	PRIMARY KEY(id)
);

CREATE TABLE side_effects (
	id_effect BIGINT,
	name	 VARCHAR(512) NOT NULL,
	PRIMARY KEY(id_effect)
);

CREATE TABLE medicine (
	id		 BIGINT,
	nome		 VARCHAR(512),
	active_principle VARCHAR(512) NOT NULL,
	PRIMARY KEY(id)
);

CREATE TABLE billing (
	id		 BIGINT,
	total		 BIGINT NOT NULL,
	data_billing	 TIMESTAMP NOT NULL,
	current_payment BIGINT,
	status		 BOOL,
	PRIMARY KEY(id)
);

CREATE TABLE payment (
	id	 BIGINT,
	amount	 BIGINT NOT NULL,
	data	 TIMESTAMP NOT NULL,
	type	 VARCHAR(512) NOT NULL,
	billing_id BIGINT,
	PRIMARY KEY(id,billing_id)
);

CREATE TABLE medical_especialization (
	id	 BIGINT,
	nome VARCHAR(512) NOT NULL,
	PRIMARY KEY(id)
);

CREATE TABLE posology (
	dose		 BIGINT NOT NULL,
	frequency	 BIGINT NOT NULL,
	medicine_id	 BIGINT,
	prescriptions_id BIGINT,
	PRIMARY KEY(medicine_id,prescriptions_id)
);

CREATE TABLE contract_employee (
	id	 BIGINT,
	data	 TIMESTAMP NOT NULL,
	duration	 DATE NOT NULL,
	person_id BIGINT,
	PRIMARY KEY(person_id)
);

CREATE TABLE person (
	id	 BIGINT,
	nome	 VARCHAR(512) NOT NULL,
	contact	 BIGINT NOT NULL,
	address	 VARCHAR(512) NOT NULL,
	email	 VARCHAR(512) NOT NULL,
	password VARCHAR(512) NOT NULL,
	username VARCHAR(512) NOT NULL,
	PRIMARY KEY(id)
);

CREATE TABLE severity (
	severity		 BIGINT,
	ocurrency		 BIGINT,
	medicine_id		 BIGINT,
	side_effects_id_effect BIGINT,
	PRIMARY KEY(medicine_id,side_effects_id_effect)
);

CREATE TABLE nurse_role (
	role				 VARCHAR(512),
	surgeries_id			 BIGINT,
	nurse_contract_employee_person_id BIGINT,
	PRIMARY KEY(surgeries_id,nurse_contract_employee_person_id)
);

CREATE TABLE medical_especialization_medical_especialization (
	medical_especialization_id	 BIGINT,
	medical_especialization_id1 BIGINT NOT NULL,
	PRIMARY KEY(medical_especialization_id)
);

CREATE TABLE doctor_medical_especialization (
	doctor_contract_employee_person_id BIGINT,
	medical_especialization_id	 BIGINT NOT NULL,
	PRIMARY KEY(doctor_contract_employee_person_id)
);

CREATE TABLE hospitalization_prescriptions (
	hospitalization_id BIGINT,
	prescriptions_id	 BIGINT NOT NULL,
	PRIMARY KEY(hospitalization_id)
);

CREATE TABLE appointment_prescriptions (
	appointment_id	 BIGINT,
	prescriptions_id BIGINT NOT NULL,
	PRIMARY KEY(appointment_id)
);

CREATE TABLE nurse_appointment (
	nurse_contract_employee_person_id BIGINT,
	appointment_id			 BIGINT,
	PRIMARY KEY(nurse_contract_employee_person_id,appointment_id)
);

ALTER TABLE pacient ADD CONSTRAINT pacient_fk1 FOREIGN KEY (person_id) REFERENCES person(id);
ALTER TABLE doctor ADD CONSTRAINT doctor_fk1 FOREIGN KEY (contract_employee_person_id) REFERENCES contract_employee(person_id);
ALTER TABLE nurse ADD CONSTRAINT nurse_fk1 FOREIGN KEY (contract_employee_person_id) REFERENCES contract_employee(person_id);
ALTER TABLE assistants ADD CONSTRAINT assistants_fk1 FOREIGN KEY (contract_employee_person_id) REFERENCES contract_employee(person_id);
ALTER TABLE surgeries ADD CONSTRAINT surgeries_fk1 FOREIGN KEY (doctor_contract_employee_person_id) REFERENCES doctor(contract_employee_person_id);
ALTER TABLE surgeries ADD CONSTRAINT surgeries_fk2 FOREIGN KEY (hospitalization_id) REFERENCES hospitalization(id);
ALTER TABLE hospitalization ADD UNIQUE (billing_id);
ALTER TABLE hospitalization ADD CONSTRAINT hospitalization_fk1 FOREIGN KEY (assistants_contract_employee_person_id) REFERENCES assistants(contract_employee_person_id);
ALTER TABLE hospitalization ADD CONSTRAINT hospitalization_fk2 FOREIGN KEY (billing_id) REFERENCES billing(id);
ALTER TABLE hospitalization ADD CONSTRAINT hospitalization_fk3 FOREIGN KEY (pacient_person_id) REFERENCES pacient(person_id);
ALTER TABLE hospitalization ADD CONSTRAINT hospitalization_fk4 FOREIGN KEY (nurse_contract_employee_person_id) REFERENCES nurse(contract_employee_person_id);
ALTER TABLE appointment ADD CONSTRAINT appointment_fk1 FOREIGN KEY (assistants_contract_employee_person_id) REFERENCES assistants(contract_employee_person_id);
ALTER TABLE appointment ADD CONSTRAINT appointment_fk2 FOREIGN KEY (billing_id) REFERENCES billing(id);
ALTER TABLE appointment ADD CONSTRAINT appointment_fk3 FOREIGN KEY (doctor_contract_employee_person_id) REFERENCES doctor(contract_employee_person_id);
ALTER TABLE appointment ADD CONSTRAINT appointment_fk4 FOREIGN KEY (pacient_person_id) REFERENCES pacient(person_id);
ALTER TABLE payment ADD CONSTRAINT payment_fk1 FOREIGN KEY (billing_id) REFERENCES billing(id);
ALTER TABLE posology ADD CONSTRAINT posology_fk1 FOREIGN KEY (medicine_id) REFERENCES medicine(id);
ALTER TABLE posology ADD CONSTRAINT posology_fk2 FOREIGN KEY (prescriptions_id) REFERENCES prescriptions(id);
ALTER TABLE contract_employee ADD CONSTRAINT contract_employee_fk1 FOREIGN KEY (person_id) REFERENCES person(id);
ALTER TABLE person ADD UNIQUE (contact, email, username);
ALTER TABLE severity ADD CONSTRAINT severity_fk1 FOREIGN KEY (medicine_id) REFERENCES medicine(id);
ALTER TABLE severity ADD CONSTRAINT severity_fk2 FOREIGN KEY (side_effects_id_effect) REFERENCES side_effects(id_effect);
ALTER TABLE nurse_role ADD CONSTRAINT nurse_role_fk1 FOREIGN KEY (surgeries_id) REFERENCES surgeries(id);
ALTER TABLE nurse_role ADD CONSTRAINT nurse_role_fk2 FOREIGN KEY (nurse_contract_employee_person_id) REFERENCES nurse(contract_employee_person_id);
ALTER TABLE medical_especialization_medical_especialization ADD CONSTRAINT medical_especialization_medical_especialization_fk1 FOREIGN KEY (medical_especialization_id) REFERENCES medical_especialization(id);
ALTER TABLE medical_especialization_medical_especialization ADD CONSTRAINT medical_especialization_medical_especialization_fk2 FOREIGN KEY (medical_especialization_id1) REFERENCES medical_especialization(id);
ALTER TABLE doctor_medical_especialization ADD CONSTRAINT doctor_medical_especialization_fk1 FOREIGN KEY (doctor_contract_employee_person_id) REFERENCES doctor(contract_employee_person_id);
ALTER TABLE doctor_medical_especialization ADD CONSTRAINT doctor_medical_especialization_fk2 FOREIGN KEY (medical_especialization_id) REFERENCES medical_especialization(id);
ALTER TABLE hospitalization_prescriptions ADD UNIQUE (prescriptions_id);
ALTER TABLE hospitalization_prescriptions ADD CONSTRAINT hospitalization_prescriptions_fk1 FOREIGN KEY (hospitalization_id) REFERENCES hospitalization(id);
ALTER TABLE hospitalization_prescriptions ADD CONSTRAINT hospitalization_prescriptions_fk2 FOREIGN KEY (prescriptions_id) REFERENCES prescriptions(id);
ALTER TABLE appointment_prescriptions ADD UNIQUE (prescriptions_id);
ALTER TABLE appointment_prescriptions ADD CONSTRAINT appointment_prescriptions_fk1 FOREIGN KEY (appointment_id) REFERENCES appointment(id);
ALTER TABLE appointment_prescriptions ADD CONSTRAINT appointment_prescriptions_fk2 FOREIGN KEY (prescriptions_id) REFERENCES prescriptions(id);
ALTER TABLE nurse_appointment ADD CONSTRAINT nurse_appointment_fk1 FOREIGN KEY (nurse_contract_employee_person_id) REFERENCES nurse(contract_employee_person_id);
ALTER TABLE nurse_appointment ADD CONSTRAINT nurse_appointment_fk2 FOREIGN KEY (appointment_id) REFERENCES appointment(id);

