CREATE OR REPLACE VIEW ExperimentsView AS
       SELECT id,
              projname,
              session,
              operation,
              username,
              ts,
              success,
              log1,
              log2
       FROM Experiments;


/*Prevent insert into the id which is a serial and inserts into serials are evil and
  tend to break stuff in a really bad fashion*/
CREATE OR REPLACE RULE ExperimentsViewInsert AS ON INSERT TO ExperimentsView DO INSTEAD
INSERT INTO Experiments (projname,
                         session,
                         operation,
                         username,
                         ts,
                         success,
                         log1,
                         log2)
            VALUES (NEW.projname,
                    NEW.session,
                    NEW.operation,
                    NEW.username,
                    NEW.ts,
                    NEW.success,
                    NEW.log1,
                    NEW.log2)
            RETURNING id, projname, session, operation, username, ts, success, log1, log2;


CREATE OR REPLACE VIEW SeleneseCommandsView AS
       SELECT expid,
              ctr,
              tcname,
              command,
              target,
              value
       FROM SeleneseCommands;

/* Needed function and not special view as this could be the first/0st entry for that experiment/ctr key */
CREATE OR REPLACE FUNCTION getHighestSeleneseCommandCounter(experiment integer) RETURNS INTEGER AS $$
       SELECT COALESCE(max(ctr),0) AS currentCounter FROM SeleneseCommandsView WHERE expid = experiment;
$$ LANGUAGE SQL;


CREATE OR REPLACE RULE SeleneseCommandsViewInsert AS ON INSERT TO SeleneseCommandsView DO INSTEAD
INSERT INTO SeleneseCommands (expid,
                              ctr,
                              tcname,
                              command,
                              target,
                              value)
       VALUES (NEW.expid,
               getHighestSeleneseCommandCounter(NEW.expid) + 1,
               NEW.tcname,
               NEW.command,
               NEW.target,
               NEW.value)
       RETURNING expid, ctr, tcname, command, target, value;


CREATE OR REPLACE VIEW HttpRequestsView AS
       SELECT expid,
              selcmdctr,
              ctr,
              ts,
              url,
              method
       FROM HttpRequests;


/* Needed function and not special view as this could be the first/0st entry for that experiment/ctr key */
CREATE OR REPLACE FUNCTION getHighestHttpRequestCounter(experiment integer,selenesecommand integer) RETURNS INTEGER AS $$
       SELECT COALESCE(max(ctr),0) AS currentCounter FROM HTTPRequestsView WHERE expid = experiment AND selcmdctr = selenesecommand;
$$ LANGUAGE SQL;


CREATE OR REPLACE RULE HttpRequestsViewInsert AS ON INSERT TO HttpRequestsView DO INSTEAD
INSERT INTO HTTPRequests (expid, 
                          selcmdctr,
                          ctr,
                          ts,
                          url,
                          method) 
       VALUES (NEW.expid,
              NEW.selcmdctr,     
              getHighestHttpRequestCounter(NEW.expid, NEw.selcmdctr) + 1,
              NEW.ts,
              NEW.url,
              NEW.method)
       RETURNING expid, 
                 selcmdctr, 
                 ctr, 
                 ts, 
                 url, 
                 method;


CREATE OR REPLACE VIEW XdebugDumpsView AS
       SELECT expid,
              selcmdctr,
              httpreqctr,
              content
       FROM XdebugDumps;


CREATE OR REPLACE VIEW XdebugDumpsRacoonView AS
       SELECT expid,
              selcmdctr,
              httpreqctr,
              name,
              content
       FROM XdebugDumps;


DROP VIEW IF EXISTS RaceSuspectsView;
CREATE OR REPLACE VIEW RaceSuspectsView AS
       SELECT id,
              set_id,
              sel_expid,     
              sel_selcmdctr,
              sel_httpreqctr,
              sel_query,
              chg_expid,
              chg_selcmdctr,
              chg_httpreqctr,
              chg_query,
              timedelta
       FROM RaceSuspects;


CREATE OR REPLACE RULE RaceSuspectsViewInsert AS ON INSERT TO RaceSuspectsView DO INSTEAD
INSERT INTO RaceSuspects (set_id,
                          sel_expid,     
                          sel_selcmdctr,
                          sel_httpreqctr,
                          sel_query,
                          chg_expid,
                          chg_selcmdctr,
                          chg_httpreqctr,
                          chg_query,
                          timedelta)
            VALUES (NEW.set_id,
                    NEW.sel_expid,     
                    NEW.sel_selcmdctr,
                    NEW.sel_httpreqctr,
                    NEW.sel_query,
                    NEW.chg_expid,
                    NEW.chg_selcmdctr,
                    NEW.chg_httpreqctr,
                    NEW.chg_query,
                    NEW.timedelta)
            RETURNING id,
                      set_id,
                      sel_expid,     
                      sel_selcmdctr,
                      sel_httpreqctr,
                      sel_query,
                      chg_expid,
                      chg_selcmdctr,
                      chg_httpreqctr,
                      chg_query,
                      timedelta;
             
DROP VIEW IF EXISTS RaceTestsView;
CREATE OR REPLACE VIEW RaceTestsView AS
       SELECT id,
              testedSuspect,
              ts,
              request_count,
              success_count,
              success_run_count,
              lssuccess_count,
              lpsuccess_count,
              start_time_comp_ref,
              end_time_comp_ref,
              start_time_testing,
              end_time_testing,
              start_time_eval,
              end_time_eval,
              start_time,
              end_time,
              check_type
       FROM RaceTests;


CREATE OR REPLACE RULE RaceTestsInsert AS ON INSERT TO RaceTestsView 
DO INSTEAD 
(
   INSERT INTO Tests DEFAULT VALUES;
   INSERT INTO RaceTests (id,
                          testedSuspect,
                          ts,
                          request_count,
                          success_count,
                          success_run_count,
                          lssuccess_count,
                          lpsuccess_count,
                          start_time,
                          end_time,
                          start_time_comp_ref,
                          end_time_comp_ref,
                          start_time_testing,
                          end_time_testing,
                          start_time_eval,
                          end_time_eval,
                          check_type)
           VALUES (currval('tests_id_seq'),
                   NEW.testedSuspect,
                   NEW.ts,
                   NEW.request_count,
                   NEW.success_count,
                   NEW.success_run_count,
                   NEW.lssuccess_count,
                   NEW.lpsuccess_count,
                   NEW.start_time,
                   NEW.end_time,
                   NEW.start_time_comp_ref,
                   NEW.end_time_comp_ref,
                   NEW.start_time_testing,
                   NEW.end_time_testing,
                   NEW.start_time_eval,
                   NEW.end_time_eval,
                   NEW.check_type)
           RETURNING id,
                     testedSuspect,
                     ts,
                     request_count,
                     success_count, 
                     success_run_count, 
                     lssuccess_count, 
                     lpsuccess_count,
                     start_time,
                     end_time,
                     start_time_comp_ref,
                     end_time_comp_ref,
                     start_time_testing,
                     end_time_testing,
                     start_time_eval,
                     end_time_eval,
                     check_type
);

DROP VIEW IF EXISTS LitmusTestsView;
CREATE OR REPLACE VIEW LitmusTestsView AS
       SELECT id,
              experiment_id,
              success_run_count,
              type
       FROM LitmusTests;


CREATE OR REPLACE RULE LitmusTestsInsert AS ON INSERT TO LitmusTestsView 
DO INSTEAD
(
   INSERT INTO Tests DEFAULT VALUES;
   INSERT INTO LitmusTests (id,
                            experiment_id,
                            success_run_count,
                            type)
          VALUES (currval('tests_id_seq'),
                  NEW.experiment_id,
                  NEW.success_run_count,
                  NEW.type)
          RETURNING id, experiment_id, success_run_count, type
);
                       
DROP VIEW IF EXISTS TestXdebugsView;
CREATE OR REPLACE VIEW TestXdebugsView AS
       SELECT testid,
              name,
              content
       FROM TestXdebugs;


CREATE OR REPLACE RULE TestXdebugsViewInsert AS ON INSERT TO TestXdebugsView DO INSTEAD
INSERT INTO TestXdebugs (testid,
                         name,
                         content)
            VALUES (NEW.testid,
                    NEW.name,
                    NEW.content)
            RETURNING testid, name, content;
