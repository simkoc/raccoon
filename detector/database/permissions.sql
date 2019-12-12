GRANT SELECT ON RaceSuspectsView,
                RaceTestsView,
                TestXdebugsView,
		    LitmusTestsView,
                ExperimentsView,
                SeleneseCommandsView,
                HttpRequestsView,
                XdebugDumpsView,
                XdebugDumpsRacoonView
             TO trueschottsman;


GRANT INSERT ON RaceSuspectsView,
                RaceTestsView,
		    LitmusTestsView,
                TestXdebugsView,
                ExperimentsView,
                SeleneseCommandsView,
                HttpRequestsView,
                XdebugDumpsView,
                XdebugDumpsRacoonView
             TO trueschottsman;

/*GRANT SELECT ON xdebugdumpsracoonview
               TO trueschottsman;*/

GRANT USAGE, SELECT ON SEQUENCE racesuspects_id_seq,
				tests_id_seq, experiments_id_seq
      TO trueschottsman;


/*GRANT select, insert ON xdebugdumpsracoonview TO trueschottsman;*/
