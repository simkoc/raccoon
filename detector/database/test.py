import postgres as db_interface

with db_interface.get_connection("localhost", "trueschottsman", "woulddothat", "secsac") as con:
        success = db_interface.get_experiment_success(con, 2)
success = bool(success[0])
print "That is interesting"
if success != True:
    print "Interessant"