USE IGSD;

ALTER TABLE IGSDProfiles ADD COLUMN IF NOT EXISTS occupied BOOLEAN DEFAULT False;
ALTER TABLE IGSDProfiles ADD COLUMN IF NOT EXISTS stats_avg FLOAT DEFAULT 0.0;

UPDATE IGSDProfiles SET stats_avg = (agility + defense + endurance + luck + strength)/5.0 WHERE stats_avg = 0.0;

/*ALTER TABLE IGSDProfiles ALTER occupied SET DEFAULT False;*/

CREATE TABLE IF NOT EXISTS IGSDEconomy (u_ID              BIGINT UNSIGNED NOT NULL UNIQUE PRIMARY KEY,
                                        builder_count     INT UNSIGNED NOT NULL DEFAULT 0,
										builder_tier      INT UNSIGNED NOT NULL DEFAULT 0,
										builder_limit_t0  INT UNSIGNED NOT NULL DEFAULT 0,
										builder_limit_t1  INT UNSIGNED NOT NULL DEFAULT 0,
										builder_limit_t2  INT UNSIGNED NOT NULL DEFAULT 0,
										builder_limit_t3  INT UNSIGNED NOT NULL DEFAULT 0,
										builder_limit_t4  INT UNSIGNED NOT NULL DEFAULT 0,
										builder_limit_t5  INT UNSIGNED NOT NULL DEFAULT 0,
										crafter_count     INT UNSIGNED NOT NULL DEFAULT 0,
										crafter_tier      INT UNSIGNED NOT NULL DEFAULT 0,
										crafter_limit_t0  INT UNSIGNED NOT NULL DEFAULT 0,
										crafter_limit_t1  INT UNSIGNED NOT NULL DEFAULT 0,
										crafter_limit_t2  INT UNSIGNED NOT NULL DEFAULT 0,
										crafter_limit_t3  INT UNSIGNED NOT NULL DEFAULT 0,
										crafter_limit_t4  INT UNSIGNED NOT NULL DEFAULT 0,
										crafter_limit_t5  INT UNSIGNED NOT NULL DEFAULT 0,
										hospital_count    INT UNSIGNED NOT NULL DEFAULT 0,
										hospital_tier     INT UNSIGNED NOT NULL DEFAULT 0,
										hospital_limit_t0 INT UNSIGNED NOT NULL DEFAULT 0,
										hospital_limit_t1 INT UNSIGNED NOT NULL DEFAULT 0,
										hospital_limit_t2 INT UNSIGNED NOT NULL DEFAULT 0,
										hospital_limit_t3 INT UNSIGNED NOT NULL DEFAULT 0,
										hospital_limit_t4 INT UNSIGNED NOT NULL DEFAULT 0,
										hospital_limit_t5 INT UNSIGNED NOT NULL DEFAULT 0,
										keygen_count      INT UNSIGNED NOT NULL DEFAULT 0,
										keygen_tier       INT UNSIGNED NOT NULL DEFAULT 0,
										keygen_limit_t0   INT UNSIGNED NOT NULL DEFAULT 1,
										keygen_limit_t1   INT UNSIGNED NOT NULL DEFAULT 0,
										keygen_limit_t2   INT UNSIGNED NOT NULL DEFAULT 0,
										keygen_limit_t3   INT UNSIGNED NOT NULL DEFAULT 0,
										keygen_limit_t4   INT UNSIGNED NOT NULL DEFAULT 0,
										keygen_limit_t5   INT UNSIGNED NOT NULL DEFAULT 0,
										research_count    INT UNSIGNED NOT NULL DEFAULT 0,
										research_tier     INT UNSIGNED NOT NULL DEFAULT 0,
										research_limit_t0 INT UNSIGNED NOT NULL DEFAULT 1,
										research_limit_t1 INT UNSIGNED NOT NULL DEFAULT 0,
										research_limit_t2 INT UNSIGNED NOT NULL DEFAULT 0,
										research_limit_t3 INT UNSIGNED NOT NULL DEFAULT 0,
										research_limit_t4 INT UNSIGNED NOT NULL DEFAULT 0,
										research_limit_t5 INT UNSIGNED NOT NULL DEFAULT 0,
										team_count        INT UNSIGNED NOT NULL DEFAULT 0,
										team_tier         INT UNSIGNED NOT NULL DEFAULT 0,
										team_limit_t0     INT UNSIGNED NOT NULL DEFAULT 1,
										team_limit_t1     INT UNSIGNED NOT NULL DEFAULT 0,
										team_limit_t2     INT UNSIGNED NOT NULL DEFAULT 0,
										team_limit_t3     INT UNSIGNED NOT NULL DEFAULT 0,
										team_limit_t4     INT UNSIGNED NOT NULL DEFAULT 0,
										team_limit_t5     INT UNSIGNED NOT NULL DEFAULT 0,
										worker_count      INT UNSIGNED NOT NULL DEFAULT 0,
										worker_tier       INT UNSIGNED NOT NULL DEFAULT 0,
										worker_limit_t0   INT UNSIGNED NOT NULL DEFAULT 0,
										worker_limit_t1   INT UNSIGNED NOT NULL DEFAULT 0,
										worker_limit_t2   INT UNSIGNED NOT NULL DEFAULT 0,
										worker_limit_t3   INT UNSIGNED NOT NULL DEFAULT 0,
										worker_limit_t4   INT UNSIGNED NOT NULL DEFAULT 0,
										worker_limit_t5   INT UNSIGNED NOT NULL DEFAULT 0);

INSERT IGNORE INTO IGSDEconomy (u_ID) SELECT u_ID FROM IGSDUsers;

CREATE TABLE IF NOT EXISTS IGSDKeyGenWorkers (u_ID          BIGINT UNSIGNED NOT NULL UNIQUE PRIMARY KEY,
                                              tier_0_slot_1 UUID,
											  tier_0_slot_2 UUID,
											  tier_0_slot_3 UUID,
											  tier_0_slot_4 UUID,
											  tier_0_slot_5 UUID,
											  tier_1_slot_1 UUID,
											  tier_1_slot_2 UUID,
											  tier_1_slot_3 UUID,
											  tier_1_slot_4 UUID,
											  tier_1_slot_5 UUID,
											  tier_2_slot_1 UUID,
											  tier_2_slot_2 UUID,
											  tier_2_slot_3 UUID,
											  tier_2_slot_4 UUID,
											  tier_2_slot_5 UUID,
											  tier_3_slot_1 UUID,
											  tier_3_slot_2 UUID,
											  tier_3_slot_3 UUID,
											  tier_3_slot_4 UUID,
											  tier_3_slot_5 UUID,
											  tier_4_slot_1 UUID,
											  tier_4_slot_2 UUID,
											  tier_4_slot_3 UUID,
											  tier_4_slot_4 UUID,
											  tier_4_slot_5 UUID,
											  tier_5_slot_1 UUID,
											  tier_5_slot_2 UUID,
											  tier_5_slot_3 UUID,
											  tier_5_slot_4 UUID,
											  tier_5_slot_5 UUID);

INSERT IGNORE INTO IGSDKeyGenWorkers (u_ID) SELECT u_ID FROM IGSDUsers;


CREATE TABLE IF NOT EXISTS  IGSDInventory (u_ID            BIGINT UNSIGNED NOT NULL UNIQUE PRIMARY KEY,
										   dust            BIGINT UNSIGNED NOT NULL DEFAULT 0,
										   t0_armor_count  INT UNSIGNED NOT NULL DEFAULT 0,
										   t0_key_count    INT UNSIGNED NOT NULL DEFAULT 1,
										   t0_weapon_count INT UNSIGNED NOT NULL DEFAULT 0,
										   t1_armor_count  INT UNSIGNED NOT NULL DEFAULT 0,
										   t1_key_count    INT UNSIGNED NOT NULL DEFAULT 0,
										   t1_weapon_count INT UNSIGNED NOT NULL DEFAULT 0,
										   t2_armor_count  INT UNSIGNED NOT NULL DEFAULT 0,
										   t2_key_count    INT UNSIGNED NOT NULL DEFAULT 0,
										   t2_weapon_count INT UNSIGNED NOT NULL DEFAULT 0,
										   t3_armor_count  INT UNSIGNED NOT NULL DEFAULT 0,
										   t3_key_count    INT UNSIGNED NOT NULL DEFAULT 0,
										   t3_weapon_count INT UNSIGNED NOT NULL DEFAULT 0,
										   t4_armor_count  INT UNSIGNED NOT NULL DEFAULT 0,
										   t4_key_count    INT UNSIGNED NOT NULL DEFAULT 0,
										   t4_weapon_count INT UNSIGNED NOT NULL DEFAULT 0,
										   t5_armor_count  INT UNSIGNED NOT NULL DEFAULT 0,
										   t5_key_count    INT UNSIGNED NOT NULL DEFAULT 0,
										   t5_weapon_count INT UNSIGNED NOT NULL DEFAULT 0);

INSERT IGNORE INTO IGSDInventory (u_ID) SELECT u_ID FROM IGSDUsers;
