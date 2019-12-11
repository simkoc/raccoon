ALTER TABLE RaceSuspects ADD COLUMN set_id integer;

ALTER TABLE RaceTests ADD COLUMN start_time_comp_ref timestamp;

ALTER TABLE RaceTests ADD COLUMN end_time_comp_ref timestamp;

ALTER TABLE RaceTests ADD COLUMN start_time_testing timestamp;

ALTER TABLE RaceTests ADD COLUMN end_time_testing timestamp;

ALTER TABLE RaceTests ADD COLUMN start_time_eval timestamp;

ALTER TABLE RaceTests ADD COLUMN end_time_eval timestamp;
