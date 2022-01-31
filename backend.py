import pyrebase
import random
import time
import json
import os
import re
from uuid import uuid4
from datetime import datetime
import coloredlogs, logging
import traceback
logger = logging.getLogger("sysc3010")
coloredlogs.install(level='DEBUG', logger=logger)


class Lab4db():
    def __init__(self,config, email=None, firstname=None, lastname=None, fakeid: int = None):
        self._firebase =pyrebase.initialize_app(config)
        self._db = self._firebase.database()
        self._fakeid = '' if fakeid is None else str(fakeid)
        self.__load_user(email,firstname,lastname)
        self.__register_device()
    
    def __led_last_update(self,device_id):
        try:
            self._db.child('devices').child(device_id).child('leds').child('last_update').set(datetime.now().strftime("%Y%m%d%H%M%S"))
        except Exception as e:
            logger.error(f"Error updating lastupdate on firebase. {e}")
    
    def __load_user(self, email= None, firstname= None, lastname= None):
        if email is None:
            email = input("Enter your email: ")
        if firstname is None:
            firstname = input("Enter your first name: ")
        if lastname is None:
            lastname = input("Enter your last name: ")
        users=self._db.child('users').get()
        if users.val() is not None:
            user = [user for user in users if email == user.val()['email']]
            if user == []:
                self._user = self.__register_new_user(email,firstname,lastname)
            else:
                self._user = dict(
                    id=user[0].key(),
                    email=user[0].val()['email'],
                    firstname=user[0].val()['firstname'],
                    lastname=user[0].val()['lastname'],
                    )
        else:
            self._user = self.__register_new_user(email,firstname,lastname)
    
    def __register_new_user(self, email, firstname, lastname):
        id = str(uuid4())
        try:
            self._db.child('users').child(id).set(
                dict(
                    email= email,
                    firstname= firstname,
                    lastname= lastname
                    )
                )
            return dict(id=id, email=email, firstname=firstname, lastname=lastname)
        except Exception as e:
            raise ConnectionError("Error registering new user. {e}")
    
    def __register_device(self):
        if not os.path.isfile('/proc/cpuinfo'):
            logger.debug("File is not being executed from a RPi. Device info is an empty dict")
            self._device_info = {}
            return
        try:
            data = dict()
            keywords = ['Serial','Hardware','Revision','Model']
            with open('/proc/cpuinfo', 'r') as f:
                for line in f:
                    for keyword in keywords :
                        lines = line.split(': ')
                        if re.sub(r'\s','',lines[0]) == keyword:
                            data[keyword.lower()] = re.sub(r'\s','',lines[1])
                f.close()
            if not "Raspberry" in data['model']:
                logger.debug("Registering device should be done from a Raspberry pi.")
                self._device_info = {}
                return
            if len(data) == 4:
                data['serial']+=self._fakeid
                rpiserial=data['serial']
                data['owner'] = self._user['id']
                data['authorized_users'] = [self._user['id'] ]
                try:
                    if rpiserial in self._db.child('devices').shallow().get().val():
                        logger.debug("Device already exist on database.")
                        self._device_info = data
                        return
                except Exception as e:
                    logger.debug("Problems querying database: it was probably empty.")
                self._db.child('devices').child(rpiserial).child('device_info').set(data)
                ledids=[ledn+1 for ledn in range(64)]
                brightled = [10,11,14,15,18,19,22,23,33,40,42,47,51,52,53,54]
                brightcolor=[random.randint(50,255),random.randint(50,255),random.randint(50,255)]
                for ledn in ledids:
                    ledcolor = [0,0,0] if ledn not in brightled else brightcolor
                    self._db.child('devices').child(rpiserial).child('leds').child(ledn).set(ledcolor)
                self.__led_last_update(rpiserial)
                self._device_info = data
                
        except Exception as e:
            logger.error(f"Something went wrong when registering device. {e}")
            logger.error(traceback.format_exc())            
    
    def add_authorized_users(self,email):
        if self._device_info == {}:
            logger.info("Adding authorized users should be done from the raspberry pi with a registered device")
            return
        valid_user = False
        users=self._db.child('users').get()
        for user in users:
            if email in user.val()['email']:
                valid_user = True
                userid = user.key()
        if valid_user:
            authorized_users = self._db.child('devices').child(self._device_info['serial']).child('device_info').child('authorized_users').get()
            if userid in authorized_users.val():
                logger.debug(f"{email} already is an authorized user.")
            else:
                authorizedlist = authorized_users.val()
                authorizedlist.append(userid)
                try:
                    self._db.child('devices').child(self._device_info['serial']).child('device_info').child('authorized_users').set(authorizedlist)
                    self._device_info['authorized_users'] = authorizedlist
                    logger.debug(f"{email} added to list of authorized users")
                except Exception as e:
                    logger.error(f"Something went wrong authorizing user: {e}.")                
        else:
            logger.warning(f"User {email} does not exist in database. User was not authorized.")
    
    def remove_authorized_users(self,email):
        if self._device_info == {}:
            logger.info("Removing authorized users should be done from the raspberry pi with a registered device")
            return
        valid_user = False
        users=self._db.child('users').get()
        for user in users:
            if email in user.val()['email']:
                valid_user = True
                userid = user.key()
        if valid_user:
            authorized_users = self._db.child('devices').child(self._device_info['serial']).child('device_info').child('authorized_users').get()
            authorizedlist = authorized_users.val()
            if userid in authorizedlist:                
                try:
                    authorizedlist.remove(userid)
                    self._db.child('devices').child(self._device_info['serial']).child('device_info').child('authorized_users').set(authorizedlist)
                    self._device_info['authorized_users'] = authorizedlist
                    logger.debug(f"{email} removed to list of authorized users")                   
                except Exception as e:
                    logger.error(f"Something went wrong authorizing user: {e}.")                
        else:
            logger.warning(f"User {email} does not exist in database.")
            
    def get_my_devices(self):
        self._my_device_ids = []
        devices = self._db.child('devices').get()
        for device in devices:
            if self._user['id'] in device.val()['device_info']['authorized_users']:
                self._my_device_ids.append(device.key())
        logger.debug(f"I am authorized to changed these devices: {self._my_device_ids}")
    
    def get_device_owner(self, device_id):
        device_owner = ""
        try:
            owner_id = self._db.child('devices').child(device_id).child('device_info').child('owner').get().val()
            user_info = {**self._db.child('users').child(owner_id).get().val()}
            device_owner = f"{user_info['firstname'].capitalize()} {user_info['lastname'].capitalize()}"
        except Exception as e:
            logger.error("Error occured while retriving owner for device {device_id}. {e}")  
        return device_owner
    
    def get_led_color(self, device_id, id):
        ledcolor=[0,0,0]
        try:
            ledcolor = self._db.child('devices').child(device_id).child('leds').child(id).get().val()
        except Exception as e:
            logger.error(f"Could not get led color: {e}.")
        return ledcolor
        
    def get_led_status(self, device_id):
        led_colors = []
        try:
            leds=self._db.child('devices').child(device_id).child('leds').get()            
            for led in leds:
                if led.key().isnumeric():
                    led_colors.append(led.val())
        except Exception as e:
            logger.error(f"An error occured while trying to retrieve led status. {e}")
        return led_colors
    
    def is_device(self):
        if self._device_info == {}:
            return False
        else:
            return True
    
    def remove_device(self):
        try:
            logger.debug("Removing device from db")
            self._db.child('devices').child(self._device_info['serial']).remove()
        except Exception as e:
            logger.error(f"Problems removing device from db. {e}")
            
    def set_led_status (self, device_id, led_id, rgb):
        try:
            self._db.child('devices').child(device_id).child('leds').child(led_id).set(rgb)
            self.__led_last_update(device_id)
        except Exception as e:
            logger.error(f"An error occured when setting led: {e}")
            logger.error(traceback.format_exc())
    
    def get_led_last_update(self,device_id):
        try:
            lastupdate=self._db.child('devices').child(device_id).child('leds').child('last_update').get()
            return lastupdate.val()
        except Exception as e:
            logger.error("Error getting time on firebase")
            return ""

    def get_device_id(self):
        if self.is_device():
            return self._device_info['serial']
        else:
            return None

    def get_pressure_data(self, device_id):
        try:
            self._db.child('devices').child(device_id).child('pressure').get()
        except Exception as e:
            logger.error(f"An error occurred when trying to get pressure data from database. {e}")
        return
    
    def set_pressure_data(self, pressure):
        try:
            datatimestr = datetime.now().strftime("%Y%m%d%H%M%S")
            self._db.child('devices').child(self._device_info['serial']).child('pressure').child().set()
        except Exception as e:
            logger.error(f"Error occurred while trying to set pressure. {e}")
