USE IGSD;

ALTER TABLE IGSDProfiles ADD COLUMN IF NOT EXISTS occupied BOOLEAN DEFAULT False;
ALTER TABLE IGSDProfiles ADD COLUMN IF NOT EXISTS stats_avg FLOAT DEFAULT 0.0;

UPDATE IGSDProfiles SET stats_avg = (agility + defense + endurance + luck + strength)/5.0 WHERE stats_avg = 0.0;

/*ALTER TABLE IGSDProfiles ALTER occupied SET DEFAULT False;*/

CREATE TABLE IF NOT EXISTS IGSDEconomy (u_ID           BIGINT UNSIGNED NOT NULL UNIQUE PRIMARY KEY,
                                        builder_count  INT UNSIGNED NOT NULL DEFAULT 0,
										builder_level  INT UNSIGNED NOT NULL DEFAULT 1,
										builder_limit  INT UNSIGNED NOT NULL DEFAULT 1,
										crafter_count  INT UNSIGNED NOT NULL DEFAULT 0,
										crafter_level  INT UNSIGNED NOT NULL DEFAULT 0,
										crafter_limit  INT UNSIGNED NOT NULL DEFAULT 0,
										hospital_count INT UNSIGNED NOT NULL DEFAULT 0,
										hospital_level INT UNSIGNED NOT NULL DEFAULT 0,
										hospital_limit INT UNSIGNED NOT NULL DEFAULT 0,
										keygen_count   INT UNSIGNED NOT NULL DEFAULT 0,
										keygen_level   INT UNSIGNED NOT NULL DEFAULT 1,
										keygen_limit   INT UNSIGNED NOT NULL DEFAULT 1,
										research_count INT UNSIGNED NOT NULL DEFAULT 0,
										research_level INT UNSIGNED NOT NULL DEFAULT 0,
										research_limit INT UNSIGNED NOT NULL DEFAULT 0,
										team_count     INT UNSIGNED NOT NULL DEFAULT 0,
										team_level     INT UNSIGNED NOT NULL DEFAULT 1,
										team_limit     INT UNSIGNED NOT NULL DEFAULT 1,
										worker_count   INT UNSIGNED NOT NULL DEFAULT 0,
										worker_level   INT UNSIGNED NOT NULL DEFAULT 0,
										worker_limit   INT UNSIGNED NOT NULL DEFAULT 0);

INSERT IGNORE INTO IGSDEconomy (u_ID) SELECT u_ID FROM IGSDUsers;

CREATE TABLE IF NOT EXISTS IGSDKeygenWorkers (u_ID           BIGINT UNSIGNED NOT NULL UNIQUE PRIMARY KEY,
                                              level_1_slot_1 UUID,
											  level_1_slot_2 UUID,
											  level_1_slot_3 UUID,
											  level_1_slot_4 UUID,
											  level_1_slot_5 UUID,
											  level_2_slot_1 UUID,
											  level_2_slot_2 UUID,
											  level_2_slot_3 UUID,
											  level_2_slot_4 UUID,
											  level_2_slot_5 UUID,
											  level_3_slot_1 UUID,
											  level_3_slot_2 UUID,
											  level_3_slot_3 UUID,
											  level_3_slot_4 UUID,
											  level_3_slot_5 UUID,
											  level_4_slot_1 UUID,
											  level_4_slot_2 UUID,
											  level_4_slot_3 UUID,
											  level_4_slot_4 UUID,
											  level_4_slot_5 UUID,
											  level_5_slot_1 UUID,
											  level_5_slot_2 UUID,
											  level_5_slot_3 UUID,
											  level_5_slot_4 UUID,
											  level_5_slot_5 UUID,
											  level_6_slot_1 UUID,
											  level_6_slot_2 UUID,
											  level_6_slot_3 UUID,
											  level_6_slot_4 UUID,
											  level_6_slot_5 UUID);

INSERT IGNORE INTO IGSDKeygenWorkers (u_ID) SELECT u_ID FROM IGSDUsers;