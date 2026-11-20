BEGIN;
ALTER TABLE ecotech.empleado ADD COLUMN IF NOT EXISTS rut VARCHAR(10);
CREATE UNIQUE INDEX IF NOT EXISTS empleado_rut_unico
    ON ecotech.empleado (rut);
COMMIT;
