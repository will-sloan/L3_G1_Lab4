from backend import Backend
from mydbconfig import *
backend = Backend(config, email, firstname, lastname)

backend.add_authorized_users('danieltura@cmail.carleton.ca')
backend.add_authorized_users('shawaizkhan@cmail.carleton.ca')
