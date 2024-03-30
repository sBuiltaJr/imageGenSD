USE IGSD;
ALTER TABLE IGSDProfiles ADD COLUMN IF NOT EXISTS job INT DEFAULT 0;

UPDATE IGSDProfiles SET job = 4 WHERE occupied = True;

ALTER TABLE IGSDProfiles DROP COLUMN IF EXISTS occupied;

ALTER TABLE IGSDEconomy ADD COLUMN IF NOT EXISTS (research_t0_progress   INT   UNSIGNED DEFAULT 0,
												  research_t0_multiplier FLOAT          DEFAULT 0.0,
												  research_t0_target     INT   UNSIGNED DEFAULT 0,
												  research_t1_progress   INT   UNSIGNED DEFAULT 0,
												  research_t1_multiplier FLOAT          DEFAULT 0.0,
												  research_t1_target     INT   UNSIGNED DEFAULT 0,
												  research_t2_progress   INT   UNSIGNED DEFAULT 0,
												  research_t2_multiplier FLOAT          DEFAULT 0.0,
												  research_t2_target     INT   UNSIGNED DEFAULT 0,
												  research_t3_progress   INT   UNSIGNED DEFAULT 0,
												  research_t3_multiplier FLOAT          DEFAULT 0.0,
												  research_t3_target     INT   UNSIGNED DEFAULT 0,
												  research_t4_progress   INT   UNSIGNED DEFAULT 0,
												  research_t4_multiplier FLOAT          DEFAULT 0.0,
												  research_t4_target     INT   UNSIGNED DEFAULT 0,
												  research_t5_progress   INT   UNSIGNED DEFAULT 0,
												  research_t5_multiplier FLOAT          DEFAULT 0.0,
												  research_t5_target     INT   UNSIGNED DEFAULT 0);

DROP TABLE IGSDKeyGenWorkers;