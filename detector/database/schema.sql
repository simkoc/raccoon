DROP TABLE IF EXISTS RaceSuspects CASCADE;
DROP TABLE IF EXISTS RaceTests CASCADE;
DROP TABLE IF EXISTS LitmusTests CASCADE;
DROP TABLE IF EXISTS TestXdebugs CASCADE;
DROP TABLE IF EXISTS Tests CASCADE;
DROP TABLE IF EXISTS Experiments CASCADE;
DROP TABLE IF EXISTS SeleneseCommands CASCADE;
DROP TABLE IF EXISTS HttpRequests CASCADE;
DROP TABLE IF EXISTS XdebugDumps CASCADE;


CREATE TYPE HttpMethod AS ENUM ('POST', 'GET');


CREATE TABLE IF NOT EXISTS Experiments (
       id                serial,
       projname          varchar(255),
       session           varchar(255),
       operation         varchar(255),
       username          varchar(255),
       ts                timestamp,      /* ts is unique and identifies all columns 3NF violation? -> no! parallel experiments! */
       success           boolean,
       PRIMARY KEY(id)
);


CREATE TABLE IF NOT EXISTS SeleneseCommands (
       expid             integer,
       ctr               integer,
       tcname            varchar(1024),
       command           varchar(1024),
       target            varchar(1024),
       value             varchar(1024),
       PRIMARY KEY(expid,ctr),
       FOREIGN KEY (expid)
       REFERENCES Experiments(id)
       ON DELETE CASCADE
);


CREATE TABLE IF NOT EXISTS HTTPRequests (
       ctr               integer,  
       expid             integer,
       selcmdctr         integer,
       ts                timestamp,
       url               varchar(2048),
       method            HttpMethod,
       PRIMARY KEY(ctr, expid, selcmdctr),
       FOREIGN KEY (expid, selcmdctr)
       REFERENCES SeleneseCommands (expid, ctr)
       ON DELETE CASCADE
 );


CREATE TABLE IF NOT EXISTS XdebugDumps (
       expid             integer,
       selcmdctr         integer,
       httpreqctr        integer,
       name              varchar(2048),  
       content           bytea,
       PRIMARY KEY (expid, selcmdctr, httpreqctr),
       FOREIGN KEY (expid, selcmdctr, httpreqctr)
       REFERENCES HTTPRequests (expid, selcmdctr, ctr)
       ON DELETE CASCADE
);


CREATE TABLE IF NOT EXISTS RaceSuspects (
       id                  serial,
       set_id              integer,
       sel_expid           integer,
       sel_selcmdctr       integer,
       sel_httpreqctr      integer,
       sel_query           text,
       chg_expid           integer,
       chg_selcmdctr       integer,
       chg_httpreqctr      integer,
       chg_query           text,
       timedelta           varchar(256),
       PRIMARY KEY(id),
       FOREIGN KEY(sel_expid, sel_selcmdctr, sel_httpreqctr)
       REFERENCES HttpRequests(expid, selcmdctr, ctr)
       ON DELETE CASCADE,
       FOREIGN KEY(chg_expid, chg_selcmdctr, chg_httpreqctr)
       REFERENCES HttpRequests(expid, selcmdctr, ctr)
       ON DELETE CASCADE
);


CREATE TABLE IF NOT EXISTS Tests (
       id                    serial,
       PRIMARY KEY(id)
);


CREATE TYPE LitmusType AS ENUM ('SEQUENTIAL', 'PARALLEL');


CREATE TABLE IF NOT EXISTS LitmusTests (
       id                    integer,
       experiment_id         integer,
       success_run_count     integer,
       type                  LitmusType,
       PRIMARY KEY(id),
       FOREIGN KEY(experiment_id)
       REFERENCES Experiments(id)
       ON DELETE CASCADE,
       FOREIGN KEY(id)
       REFERENCES Tests(id)
       ON DELETE CASCADE
);


CREATE TABLE IF NOT EXISTS RaceTests (
       id                    integer,
       testedSuspect         integer,
       ts                    timestamp,
       request_count         integer,
       success_count         integer,
       success_run_count     integer,
       lssuccess_count       integer,
       lpsuccess_count       integer,
       start_time            timestamp,
       end_time              timestamp,
       start_time_comp_ref   timestamp,
       end_time_comp_ref     timestamp,
       start_time_testing    timestamp,
       end_time_testing      timestamp,
       start_time_eval       timestamp,
       end_time_eval         timestamp,
       check_type            varchar(1024),
       PRIMARY KEY(id),
       FOREIGN KEY(id)
       REFERENCES Tests(id)
       ON DELETE CASCADE,
       FOREIGN KEY(testedSuspect)
       REFERENCES RaceSuspects(id)
       ON DELETE CASCADE
);


CREATE TABLE IF NOT EXISTS TestXdebugs (
       testid            integer,
       name              varchar(2048),
       content           bytea,
       FOREIGN KEY(testid)
       REFERENCES Tests(id)
       ON DELETE CASCADE
);
