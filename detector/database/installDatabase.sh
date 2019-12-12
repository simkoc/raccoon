#!/bin/sh

psql -d $1 < schema.sql
psql -d $1 < view.sql
psql -d $1 < permissions.sql
