/* ============================================================
   Subsystem 3 – Secure Delivery Subsystem
   PR1 Add-On Tables + Sample Data
   ============================================================ */


/* ============================================================
   DELIVERY NOTIFICATIONS
   Records when access codes are sent to recipients
   ============================================================ */

CREATE TABLE delivery_notifications (
    notification_id INT PRIMARY KEY AUTO_INCREMENT,
    code_id INT NOT NULL,
    channel ENUM('email','sms','in_app') NOT NULL,
    recipient_contact VARCHAR(255) NOT NULL,
    delivery_status ENUM('queued','sent','failed') NOT NULL DEFAULT 'queued',
    sent_at DATETIME,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (code_id) REFERENCES disclosure_access_codes(code_id)
        ON DELETE CASCADE
);


/* ============================================================
   RECIPIENT ACCESS EVENTS
   Logs attempts to use an access code
   ============================================================ */

CREATE TABLE recipient_access_events (
    event_id INT PRIMARY KEY AUTO_INCREMENT,
    code_id INT NOT NULL,
    disclosure_id INT NOT NULL,
    recipient_id INT NOT NULL,
    attempt_time DATETIME NOT NULL,
    access_result ENUM('success','denied','expired','invalid','used') NOT NULL,
    ip_address VARCHAR(45),
    user_agent VARCHAR(255),
    FOREIGN KEY (code_id) REFERENCES disclosure_access_codes(code_id)
        ON DELETE CASCADE,
    FOREIGN KEY (disclosure_id) REFERENCES disclosures(disclosure_id)
        ON DELETE CASCADE,
    FOREIGN KEY (recipient_id) REFERENCES users(user_id)
        ON DELETE CASCADE
);



/* ============================================================
   SAMPLE DATA
   ============================================================ */


/* ---------- DELIVERY NOTIFICATIONS (10 ROWS) ---------- */

INSERT INTO delivery_notifications
(code_id, channel, recipient_contact, delivery_status, sent_at) VALUES
(1,'email','recipient1@email.com','sent','2026-02-01 09:15:00'),
(2,'email','recipient2@email.com','sent','2026-02-01 09:18:00'),
(3,'sms','+12485550103','sent','2026-02-01 09:22:00'),
(4,'email','recipient4@email.com','sent','2026-02-01 09:30:00'),
(5,'in_app','recipient5@email.com','sent','2026-02-01 09:35:00'),
(6,'email','recipient6@email.com','failed',NULL),
(7,'sms','+12485550107','sent','2026-02-01 09:45:00'),
(8,'email','recipient1@email.com','sent','2026-02-03 14:35:00'),
(9,'in_app','recipient2@email.com','queued',NULL),
(10,'email','recipient3@email.com','sent','2026-02-04 11:05:00');


/* ---------- RECIPIENT ACCESS EVENTS (10 ROWS) ---------- */

INSERT INTO recipient_access_events
(code_id, disclosure_id, recipient_id, attempt_time, access_result, ip_address, user_agent) VALUES
(1,1,4,'2026-02-01 10:02:10','success','192.168.1.25','Chrome'),
(2,2,5,'2026-02-02 10:18:22','success','192.168.1.40','Chrome'),
(3,3,6,'2026-02-02 12:11:09','denied','192.168.1.77','Firefox'),
(4,4,7,'2026-02-02 12:30:55','denied','192.168.1.88','Safari'),
(5,5,8,'2026-02-03 08:22:01','success','192.168.1.12','Chrome'),
(6,6,9,'2026-02-03 09:44:17','expired','192.168.1.90','Edge'),
(7,7,10,'2026-02-03 11:09:33','success','192.168.1.67','Chrome'),
(8,8,4,'2026-02-03 14:41:05','used','192.168.1.25','Chrome'),
(9,9,5,'2026-02-04 08:15:44','invalid','192.168.1.41','Firefox'),
(10,10,6,'2026-02-04 11:12:28','success','192.168.1.77','Chrome');
