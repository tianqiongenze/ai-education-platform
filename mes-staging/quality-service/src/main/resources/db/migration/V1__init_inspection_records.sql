-- Quality inspections table
CREATE TABLE IF NOT EXISTS inspection_records (
    id                  VARCHAR(36) NOT NULL,
    production_order_id VARCHAR(255) NOT NULL,
    product_code        VARCHAR(255) NOT NULL,
    sample_size         INTEGER NOT NULL,
    passed              INTEGER NOT NULL,
    failed              INTEGER NOT NULL,
    result              VARCHAR(32) NOT NULL DEFAULT 'PENDING',
    inspector           VARCHAR(255),
    defect_type         VARCHAR(255),
    notes               TEXT,
    inspected_at        TIMESTAMP NOT NULL,
    CONSTRAINT pk_inspection_records PRIMARY KEY (id)
);
CREATE INDEX IF NOT EXISTS idx_inspection_records_order ON inspection_records (production_order_id);
CREATE INDEX IF NOT EXISTS idx_inspection_records_result ON inspection_records (result);
