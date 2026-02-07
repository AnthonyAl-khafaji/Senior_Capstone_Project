/* ============================================================
   Subsystem 2 – Selective Disclosure System
   Mental Health Selective Disclosure Web Application
   ======================================= */


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
   DISCLOSURE FIELDS TABLE
   Client will choose the fields to share
   ============================================================ */

CREATE TABLE disclosure_fields (
    therapy_id INT PRIMARY KEY AUTO_INCREMENT,
    disclosure_id INT NOT NULL,
	disclose_diagnosis BOOLEAN NOT NULL,
	disclose_meds BOOLEAN NOT NULL,
    disclose_hospitalization BOOLEAN NOT NULL,
    FOREIGN KEY (disclosure_id) REFERENCES disclosures(disclosure_id)
        ON DELETE CASCADE
);

/* ============================================================
   RECIPIENT TABLE
   This is for who recieves the information.
   Can be:  psychiatrist, therapist, disability office, or family member
   ============================================================ */

CREATE TABLE disclosure_recipient (
    diagnosis_id INT PRIMARY KEY AUTO_INCREMENT,
    disclosure_id INT NOT NULL,
    diagnosis_text VARCHAR(255) NOT NULL,
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
   ACCESS TIME TABLE
   Supports dual authentication security model
   ============================================================ */

CREATE TABLE disclosure_access_time (
    code_id INT PRIMARY KEY AUTO_INCREMENT,
    disclosure_id INT NOT NULL,
    recipient_id INT NOT NULL,
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

/* ---------- DISCLOSURE FIELDS ---------- */

INSERT INTO disclosure_fields (disclosure_id, disclose_diagnosis, disclose_meds, disclose_hospitalization) VALUES
(1,TRUE,TRUE,TRUE),
(2,TRUE,FALSE,TRUE),
(3,FALSE,TRUE,FALSE),
(4,TRUE,TRUE,TRUE),
(5,TRUE,TRUE,TRUE),
(6,FALSE,FALSE,FALSE),
(7,TRUE,TRUE,TRUE),
(8,TRUE,FALSE,TRUE),
(9,FALSE,TRUE,TRUE),
(10,TRUE,TRUE,TRUE);

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


/* ---------- EXPIRATION TIME ---------- */

INSERT INTO disclosure_access_time
(disclosure_id, recipient_id, expires_at) VALUES
(1,4,'2026-05-01 23:59:59'),
(2,5,'2026-05-01 23:59:59'),
(3,6,'2026-05-01 23:59:59'),
(4,7,'2026-05-01 23:59:59'),
(5,8,'2026-05-01 23:59:59'),
(6,9,'2026-05-01 23:59:59'),
(7,10,'2026-05-01 23:59:59'),
(8,4,'2026-05-01 23:59:59'),
(9,5,'2026-05-01 23:59:59'),
(10,6,'2026-05-01 23:59:59');
