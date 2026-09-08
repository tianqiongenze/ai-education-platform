-- Production orders table (replaces Hibernate auto-DDL; explicit schema for Flyway)
CREATE TABLE IF NOT EXISTS production_orders (
    id                 VARCHAR(36) NOT NULL,
    product_code       VARCHAR(255) NOT NULL,
    quantity           INTEGER NOT NULL,
    status             VARCHAR(32) NOT NULL DEFAULT 'CREATED',
    priority           VARCHAR(32) NOT NULL DEFAULT 'NORMAL',
    work_center        VARCHAR(255),
    assigned_operator  VARCHAR(255),
    completed_quantity INTEGER NOT NULL DEFAULT 0,
    defect_count       INTEGER NOT NULL DEFAULT 0,
    planned_start      TIMESTAMP,
    planned_end        TIMESTAMP,
    actual_start       TIMESTAMP,
    actual_end         TIMESTAMP,
    created_at         TIMESTAMP NOT NULL,
    updated_at         TIMESTAMP,
    CONSTRAINT pk_production_orders PRIMARY KEY (id)
);
CREATE INDEX IF NOT EXISTS idx_production_orders_status ON production_orders (status);
CREATE INDEX IF NOT EXISTS idx_production_orders_work_center ON production_orders (work_center);
CREATE INDEX IF NOT EXISTS idx_production_orders_operator ON production_orders (assigned_operator);
CREATE INDEX IF NOT EXISTS idx_production_orders_priority ON production_orders (priority);
