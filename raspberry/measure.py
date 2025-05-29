import database as db

db.create_tables()

with db.get_db_cursor() as cur:
    pass # TODO: insert data from data.txt once I figured out which data from shelly plug makes sense

