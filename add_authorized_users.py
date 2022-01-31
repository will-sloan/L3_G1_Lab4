from backend import Lab4db
from mydbconfig import *
db = Lab4db(config, email, firstname, lastname)

db.add_authorized_users('my_group_mate1_email@cmail.carleton.ca')
db.add_authorized_users('my_group_mate2_email@cmail.carleton.ca')