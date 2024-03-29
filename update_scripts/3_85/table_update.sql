USE IGSD;

ALTER TABLE IGSDProfiles ADD COLUMN IF NOT EXISTS armor          BIGINT DEFAULT 0;
ALTER TABLE IGSDProfiles ADD COLUMN IF NOT EXISTS weapon         BIGINT DEFAULT 0;
ALTER TABLE IGSDProfiles ADD COLUMN IF NOT EXISTS health         BIGINT DEFAULT 100;
ALTER TABLE IGSDProfiles ADD COLUMN IF NOT EXISTS dust_value     BIGINT DEFAULT 0;
ALTER TABLE IGSDProfiles ADD COLUMN IF NOT EXISTS times_upgraded BIGINT DEFAULT 0;

ALTER TABLE IGSDUsers ADD COLUMN IF NOT EXISTS dropdown_active BOOLEAN DEFAULT False;
