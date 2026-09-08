-- Inventory materials table
CREATE TABLE IF NOT EXISTS materials (
    id            VARCHAR(36) NOT NULL,
    sku           VARCHAR(255) NOT NULL,
    name          VARCHAR(255) NOT NULL,
    unit          VARCHAR(32) NOT NULL,
    quantity      INTEGER NOT NULL DEFAULT 0,
    reorder_point INTEGER NOT NULL DEFAULT 0,
    safety_stock  INTEGER NOT NULL DEFAULT 0,
    unit_cost     DOUBLE PRECISION NOT NULL DEFAULT 0,
    warehouse     VARCHAR(255),
    updated_at    TIMESTAMP NOT NULL,
    CONSTRAINT pk_materials PRIMARY KEY (id)
);
CREATE UNIQUE INDEX IF NOT EXISTS uk_materials_sku ON materials (sku);
CREATE INDEX IF NOT EXISTS idx_materials_quantity ON materials (quantity);
