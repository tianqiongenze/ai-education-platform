-- Equipment table
CREATE TABLE IF NOT EXISTS equipment (
    id              VARCHAR(36) NOT NULL,
    code            VARCHAR(255) NOT NULL,
    name            VARCHAR(255) NOT NULL,
    status          VARCHAR(32) NOT NULL DEFAULT 'IDLE',
    location        VARCHAR(255) NOT NULL,
    manufacturer    VARCHAR(255),
    model           VARCHAR(255),
    temperature     DOUBLE PRECISION NOT NULL DEFAULT 0,
    vibration       DOUBLE PRECISION NOT NULL DEFAULT 0,
    rpm             INTEGER NOT NULL DEFAULT 0,
    utilization_rate DOUBLE PRECISION NOT NULL DEFAULT 0,
    last_maintenance TIMESTAMP,
    installed_at    TIMESTAMP NOT NULL,
    CONSTRAINT pk_equipment PRIMARY KEY (id)
);
CREATE UNIQUE INDEX IF NOT EXISTS uk_equipment_code ON equipment (code);
CREATE INDEX IF NOT EXISTS idx_equipment_status ON equipment (status);
