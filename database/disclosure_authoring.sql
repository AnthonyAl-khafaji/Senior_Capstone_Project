/* ============================================================
   Subsystem 1 – Disclosure Authoring
   PR1 Database Setup + Sample Data
   Mental Health Selective Disclosure Web Application

   Notes:
   - Passwords stored as placeholder hashes (NOT plaintext)
   - Each disclosure element is stored separately to support
     selective sharing.
   ============================================================ */


/* ============================================================
   USERS TABLE
   Stores both Clients and Recipients
   ============================================================ */

CREATE TABLE users (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('client','recipient') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


/* ============================================================
   DISCLOSURES TABLE
   One disclosure record per client entry session
   ============================================================ */

CREATE TABLE disclosures (
    disclosure_id INT PRIMARY KEY AUTO_INCREMENT,
    client_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES users(user_id)
        ON DELETE CASCADE
);


/* ============================================================
   DIAGNOSES TABLE
   Multiple diagnoses per disclosure allowed
   ============================================================ */

CREATE TABLE disclosure_diagnoses (
    diagnosis_id INT PRIMARY KEY AUTO_INCREMENT,
    disclosure_id INT NOT NULL,
    diagnosis_text VARCHAR(255) NOT NULL,
    FOREIGN KEY (disclosure_id) REFERENCES disclosures(disclosure_id)
        ON DELETE CASCADE
);


/* ============================================================
   MEDICATION TABLE
   Medication + optional dosage separated
   ============================================================ */

CREATE TABLE disclosure_medications (
    medication_id INT PRIMARY KEY AUTO_INCREMENT,
    disclosure_id INT NOT NULL,
    medication_name VARCHAR(255) NOT NULL,
    dosage VARCHAR(100),
    FOREIGN KEY (disclosure_id) REFERENCES disclosures(disclosure_id)
        ON DELETE CASCADE
);


/* ============================================================
   THERAPY TABLE
   Tracks therapy participation and type
   ============================================================ */

CREATE TABLE disclosure_therapy (
    therapy_id INT PRIMARY KEY AUTO_INCREMENT,
    disclosure_id INT NOT NULL,
    in_therapy BOOLEAN NOT NULL,
    therapy_type VARCHAR(255),
    FOREIGN KEY (disclosure_id) REFERENCES disclosures(disclosure_id)
        ON DELETE CASCADE
);


/* ============================================================
   HOSPITALIZATION HISTORY TABLE
   ============================================================ */

CREATE TABLE disclosure_hospitalization (
    hospitalization_id INT PRIMARY KEY AUTO_INCREMENT,
    disclosure_id INT NOT NULL,
    has_history BOOLEAN NOT NULL,
    FOREIGN KEY (disclosure_id) REFERENCES disclosures(disclosure_id)
        ON DELETE CASCADE
);


/* ============================================================
   NOTES TABLE
   Multiple distress/impairment notes allowed
   ============================================================ */

CREATE TABLE disclosure_notes (
    note_id INT PRIMARY KEY AUTO_INCREMENT,
    disclosure_id INT NOT NULL,
    note_text TEXT NOT NULL,
    FOREIGN KEY (disclosure_id) REFERENCES disclosures(disclosure_id)
        ON DELETE CASCADE
);


/* ============================================================
   DISCLOSURE RECIPIENT MAPPING
   Tracks which recipient receives which disclosure
   ============================================================ */

CREATE TABLE disclosure_recipients (
    id INT PRIMARY KEY AUTO_INCREMENT,
    disclosure_id INT NOT NULL,
    recipient_id INT NOT NULL,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (disclosure_id) REFERENCES disclosures(disclosure_id)
        ON DELETE CASCADE,
    FOREIGN KEY (recipient_id) REFERENCES users(user_id)
        ON DELETE CASCADE
);


/* ============================================================
   ACCESS CODE TABLE
   Supports dual authentication security model
   ============================================================ */

CREATE TABLE disclosure_access_codes (
    code_id INT PRIMARY KEY AUTO_INCREMENT,
    disclosure_id INT NOT NULL,
    recipient_id INT NOT NULL,
    access_code VARCHAR(50) UNIQUE NOT NULL,
    expires_at DATETIME NOT NULL,
    used_at DATETIME,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (disclosure_id) REFERENCES disclosures(disclosure_id)
        ON DELETE CASCADE,
    FOREIGN KEY (recipient_id) REFERENCES users(user_id)
        ON DELETE CASCADE
);



/* ============================================================
   SAMPLE DATA SECTION
   ============================================================ */


/* ---------- USERS ---------- */

INSERT INTO users (email, password_hash, role) VALUES
('client1@email.com','hash1','client'),
('client2@email.com','hash2','client'),
('client3@email.com','hash3','client'),
('recipient1@email.com','hash4','recipient'),
('recipient2@email.com','hash5','recipient'),
('recipient3@email.com','hash6','recipient'),
('recipient4@email.com','hash7','recipient'),
('recipient5@email.com','hash8','recipient'),
('recipient6@email.com','hash9','recipient'),
('recipient7@email.com','hash10','recipient');


/* ---------- DISCLOSURES ---------- */

INSERT INTO disclosures (client_id) VALUES
(1),(1),(2),(2),(3),(3),(1),(2),(3),(1);


/* ---------- DIAGNOSES ---------- */

INSERT INTO disclosure_diagnoses (disclosure_id, diagnosis_text) VALUES
(1,'Generalized Anxiety Disorder'),
(1,'Major Depressive Disorder'),
(2,'ADHD'),
(3,'PTSD'),
(4,'Bipolar II Disorder'),
(5,'Social Anxiety Disorder'),
(6,'Panic Disorder'),
(7,'Obsessive Compulsive Disorder'),
(8,'Borderline Personality Disorder'),
(9,'Seasonal Affective Disorder');


/* ---------- MEDICATIONS ---------- */

INSERT INTO disclosure_medications (disclosure_id, medication_name, dosage) VALUES
(1,'Sertraline','50mg'),
(1,'Buspirone','10mg'),
(2,'Adderall','20mg'),
(3,'Fluoxetine','40mg'),
(4,'Lamotrigine','100mg'),
(5,'Propranolol','20mg'),
(6,'Alprazolam','0.5mg'),
(7,'Clomipramine','25mg'),
(8,'Quetiapine','150mg'),
(9,'Bupropion','300mg');


/* ---------- THERAPY ---------- */

INSERT INTO disclosure_therapy (disclosure_id, in_therapy, therapy_type) VALUES
(1,TRUE,'CBT'),
(2,TRUE,'DBT'),
(3,FALSE,NULL),
(4,TRUE,'Group Therapy'),
(5,TRUE,'Exposure Therapy'),
(6,FALSE,NULL),
(7,TRUE,'Psychodynamic Therapy'),
(8,TRUE,'Family Therapy'),
(9,FALSE,NULL),
(10,TRUE,'CBT');


/* ---------- HOSPITALIZATION ---------- */

INSERT INTO disclosure_hospitalization (disclosure_id, has_history) VALUES
(1,FALSE),
(2,FALSE),
(3,TRUE),
(4,FALSE),
(5,FALSE),
(6,TRUE),
(7,FALSE),
(8,TRUE),
(9,FALSE),
(10,FALSE);


/* ---------- NOTES ---------- */

INSERT INTO disclosure_notes (disclosure_id, note_text) VALUES
(1,'Difficulty concentrating during high stress'),
(2,'Struggles with time management'),
(3,'Triggers related to loud environments'),
(4,'Mood instability during seasonal changes'),
(5,'Avoids large social gatherings'),
(6,'Experiences sudden panic attacks'),
(7,'Repetitive intrusive thoughts'),
(8,'Difficulty maintaining interpersonal relationships'),
(9,'Low energy during winter months'),
(10,'Stress impacts academic performance');


/* ---------- DISCLOSURE RECIPIENTS ---------- */

INSERT INTO disclosure_recipients (disclosure_id, recipient_id) VALUES
(1,4),
(2,5),
(3,6),
(4,7),
(5,8),
(6,9),
(7,10),
(8,4),
(9,5),
(10,6);


/* ---------- ACCESS CODES ---------- */

INSERT INTO disclosure_access_codes
(disclosure_id, recipient_id, access_code, expires_at) VALUES
(1,4,'CODE123A','2026-05-01 23:59:59'),
(2,5,'CODE123B','2026-05-01 23:59:59'),
(3,6,'CODE123C','2026-05-01 23:59:59'),
(4,7,'CODE123D','2026-05-01 23:59:59'),
(5,8,'CODE123E','2026-05-01 23:59:59'),
(6,9,'CODE123F','2026-05-01 23:59:59'),
(7,10,'CODE123G','2026-05-01 23:59:59'),
(8,4,'CODE123H','2026-05-01 23:59:59'),
(9,5,'CODE123I','2026-05-01 23:59:59'),
(10,6,'CODE123J','2026-05-01 23:59:59');
