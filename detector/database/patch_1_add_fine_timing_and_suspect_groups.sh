#!/bin/bash

psql -d $1 < path_1_schema.sql
psql -d $1 < view.sql
psql -d $1 < permissions.sql
