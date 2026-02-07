/* ============================================================
   Subsystem 5 – Audit & Monitoring System
   Mental Health Selective Disclosure Web Application
   ============================================================ */


/* =========================
   DISCLOSURE ACTIVITY AUDIT
   ========================= */

CREATE TABLE audit_disclosure_activity (
    activity_id INT PRIMARY KEY AUTO_INCREMENT,
    disclosure_id INT NOT NULL,
    client_id INT NOT NULL,
    action ENUM('CREATE','EDIT','SAVE','SHARE','REVOKE','DELETE') NOT NULL,
    performed_by INT NOT NULL,
    performed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    details VARCHAR(500),
    FOREIGN KEY (disclosure_id) REFERENCES disclosures(disclosure_id) ON DELETE CASCADE,
    FOREIGN KEY (client_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (performed_by) REFERENCES users(user_id) ON DELETE CASCADE
);


/* =========================
   RECIPIENT ACCESS AUDIT
   ========================= */

CREATE TABLE audit_recipient_access (
    access_log_id INT PRIMARY KEY AUTO_INCREMENT,
    disclosure_id INT NOT NULL,
    client_id INT NOT NULL,
    recipient_id INT NOT NULL,
    access_status ENUM('SUCCESS','FAILED','EXPIRED','REVOKE') NOT NULL,
    accessed_at DATETIME NOT NULL,
    ip_address VARCHAR(45),
    user_agent VARCHAR(255),
    FOREIGN KEY (disclosure_id) REFERENCES disclosures(disclosure_id) ON DELETE CASCADE,
    FOREIGN KEY (client_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (recipient_id) REFERENCES users(user_id) ON DELETE CASCADE
);


/* =========================
   SAMPLE DATA
   ========================= */

INSERT INTO audit_disclosure_activity
(disclosure_id, client_id, action, performed_by, performed_at, details) VALUES
(1, 1, 'CREATE', 1, '2026-01-10 09:12:00', 'Created disclosure'),
(1, 1, 'SAVE', 1, '2026-01-10 09:15:00', 'Saved information'),
(2, 1, 'CREATE', 1, '2026-01-15 14:02:00', 'Created new disclosure'),
(2, 1, 'EDIT', 1, '2026-01-15 14:10:00', 'Edited disclosure'),
(3, 2, 'CREATE', 2, '2026-01-18 11:30:00', 'Created disclosure'),
(3, 2, 'SAVE', 2, '2026-01-18 11:41:00', 'Saved disclosure'),
(4, 2, 'CREATE', 2, '2026-01-22 16:20:00', 'Created disclosure'),
(4, 2, 'SHARE', 2, '2026-01-22 16:35:00', 'Shared with recipient'),
(5, 3, 'CREATE', 3, '2026-01-25 08:55:00', 'Created disclosure'),
(5, 3, 'SHARE', 3, '2026-01-25 09:05:00', 'Shared with recipient');


INSERT INTO audit_recipient_access
(disclosure_id, client_id, recipient_id, access_status, accessed_at, ip_address, user_agent) VALUES
(1, 1, 4, 'SUCCESS', '2026-01-10 10:01:12', '73.22.10.5', 'Mozilla/5.0'),
(1, 1, 4, 'SUCCESS', '2026-01-11 09:22:45', '73.22.10.5', 'Mozilla/5.0'),
(2, 1, 5, 'FAILED', '2026-01-15 15:00:02', '18.44.90.1', 'Mozilla/5.0'),
(2, 1, 5, 'SUCCESS', '2026-01-15 15:04:10', '18.44.90.1', 'Mozilla/5.0'),
(3, 2, 6, 'SUCCESS', '2026-01-18 12:10:33', '64.31.7.88', 'Mozilla/5.0'),
(4, 2, 7, 'SUCCESS', '2026-01-22 17:05:00', '64.31.7.88', 'Mozilla/5.0'),
(5, 3, 8, 'SUCCESS', '2026-01-25 09:30:11', '101.14.2.9', 'Mozilla/5.0'),
(6, 3, 9, 'REVOKE', '2026-02-02 10:05:09', '101.14.2.9', 'Mozilla/5.0'),
(7, 1, 10, 'EXPIRED', '2026-02-05 08:40:40', '22.18.44.12', 'Mozilla/5.0'),
(8, 2, 4, 'SUCCESS', '2026-02-06 14:21:55', '73.22.10.5', 'Mozilla/5.0');


/* =========================
   AUDIT LOG QUERIES
   ========================= */

SELECT activity_id, disclosure_id, action, performed_at, details
FROM audit_disclosure_activity
WHERE client_id = 1
ORDER BY performed_at DESC;

SELECT r.access_log_id, r.disclosure_id, u.email, r.access_status, r.accessed_at
FROM audit_recipient_access r
JOIN users u ON u.user_id = r.recipient_id
WHERE r.client_id = 1
ORDER BY r.accessed_at DESC;
