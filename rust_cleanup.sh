#!/bin/sh
psql -h 10.167.2.175 -p 26257 -U root -d security_audit <<'SQL'
DELETE FROM findings WHERE session_id IN (SELECT id FROM audit_sessions WHERE auditor = 'stress');
DELETE FROM audit_sessions WHERE auditor = 'stress';
SELECT count(*) AS sessions FROM audit_sessions;
SELECT count(*) AS findings FROM findings;
SQL
