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


class Backend():
    def __init__(self,config, email=None, firstname=None, lastname=None, fakeid: int = None):
        self._firebase =pyrebase.initialize_app(config)
        self._db = self._firebase.database()
        self._fakeid = '' if fakeid is None else str(fakeid)
        self.__load_user(email, firstname, lastname)
        self.__load_device_info()

    def __get_device_info(self, device_id):
        logger.debug(f"Retrieving device info for: {device_id}")
        device_info = dict()
        try:
            device_info = {**self._db.child('devices').child(device_id).child('device_info').get().val()}
        except Exception as e:
            logger.error(f"Device {device_id} does not exist in the database.")
        return device_info

    def __get_device_owner_id(self, device_id):
        logger.debug(f"Retrieving device owner id.")
        owner_id = ""
        try:
            owner_id = self._db.child('devices').child(device_id).child('device_info').child('owner').get().val()
        except Exception as e:
            logger.error(f"Error occured while retriving owner id for device {device_id}. {e}")
        return owner_id

    def __led_last_update(self,device_id):
        try:
            self._db.child('devices').child(device_id).child('leds').child('last_update').set(datetime.now().strftime("%Y%m%d%H%M%S"))
        except Exception as e:
            logger.error(f"Error updating lastupdate on firebase. {e}")

    def __load_device_info(self):
        logger.debug("Loading device information.")
        if not os.path.isfile('/proc/cpuinfo'):
            logger.debug("File is not being executed from a RPi. Device info is an empty dict.")
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
                logger.debug("File is not being executed from a RPi. Device info is an empty dict.")
                self._device_info = {}
                return
            if len(data) == 4:
                data['serial']+=self._fakeid
                rpiserial=data['serial']
                data['owner'] = self._user['id']
                data['authorized_users'] = [self._user['id'] ]
                try:
                    if rpiserial in self._db.child('devices').shallow().get().val():
                        logger.debug(f"Device already exist on database. _device_info is: {data}")
                        self._device_info = data
                        return
                except Exception as e:
                    logger.debug("Problems querying database: it was probably empty. We will create a new device entry.")
                # Create the new device entry on database and set initial values.
                self._db.child('devices').child(rpiserial).child('device_info').set(data)
                ledids=[ledn+1 for ledn in range(64)]
                brightled = [10,11,14,15,18,19,22,23,33,40,42,47,51,52,53,54]
                brightcolor=[random.randint(50,255),random.randint(50,255),random.randint(50,255)]
                for ledn in ledids:
                    ledcolor = [0,0,0] if ledn not in brightled else brightcolor
                    self._db.child('devices').child(rpiserial).child('leds').child(ledn).set(ledcolor)
                self.__led_last_update(rpiserial)
                self._device_info = data
                logger.debug(f"New device was added to the database. _device_info: {data}")
        except Exception as e:
            logger.error(f"Something went wrong when registering device. {e}")
            logger.error(traceback.format_exc())

    def __load_user(self, email=None, firstname=None, lastname=None):
        logger.debug(f"Loading user data.")
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
                self._user = self.__register_new_user(email, firstname, lastname)
            else:
                self._user = dict(
                    id=user[0].key(),
                    email=user[0].val()['email'],
                    firstname=user[0].val()['firstname'],
                    lastname=user[0].val()['lastname'],
                    )
        else:
            self._user = self.__register_new_user(email, firstname, lastname)
        logger.debug(f"User loaded: {self._user}")
    
    def __register_new_user(self, email, firstname, lastname):
        logger.debug(f"Registering new user.")
        id = str(uuid4())
        try:
            self._db.child('users').child(id).set(
                dict(
                    email= email,
                    firstname= firstname,
                    lastname= lastname
                    )
                )
            logger.debug(f"Registered new user: {firstname} {lastname}, {email}.")
            return dict(id=id, email=email, firstname=firstname, lastname=lastname)
        except Exception as e:
            raise ConnectionError("Error registering new user. {e}")

    def add_authorized_users(self, email):
        logger.debug("Adding authorized user.")
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
                logger.debug(f"{email} already is an authorized user for this device.")
            else:
                authorizedlist = authorized_users.val()
                authorizedlist.append(userid)
                try:
                    self._db.child('devices').child(self._device_info['serial']).child('device_info').child('authorized_users').set(authorizedlist)
                    self._device_info['authorized_users'] = authorizedlist
                    logger.debug(f"{email} added to list of authorized users for this device.")
                except Exception as e:
                    logger.error(f"Something went wrong authorizing user: {e}.")                
        else:
            logger.warning(f"User {email} does not exist in database. User was not authorized.")

    def clear_leds(self, device_id):
        device_info = self.__get_device_info(device_id)
        if device_info != {}:
            if self._user['id'] == device_info['owner']:
                logger.debug('Clearing all LED colors in the database.')
                for ledn in range(64):
                    try:
                        self._db.child('devices').child(device_id).child('leds').child(ledn+1).set([0,0,0])
                    except Exception as e:
                        logger.error(f"An error occurred while setting rgb color for led {ledn}. {e}")
                self.__led_last_update(device_id)
            else:
                logger.warning(f"{self._user['email']} is not authorized to clear the rgb colors for device {device_id}.")

    def get_device_id(self):
        if self.is_device():
            return self._device_info['serial']
        else:
            return None

    def get_device_owner(self, device_id):
        logger.debug(f"Retrieving device owner.")
        device_owner = ""
        try:
            owner_id = self._db.child('devices').child(device_id).child('device_info').child('owner').get().val()
            user_info = {**self._db.child('users').child(owner_id).get().val()}
            device_owner = f"{user_info['firstname'].capitalize()} {user_info['lastname'].capitalize()}"
        except Exception as e:
            logger.error(f"Error occured while retriving owner for device {device_id}. {e}")
        return device_owner

    def get_led_color(self, device_id, id):
        ledcolor=[0,0,0]
        try:
            ledcolor = self._db.child('devices').child(device_id).child('leds').child(id).get().val()
        except Exception as e:
            logger.error(f"Could not get led color: {e}.")
        return ledcolor

    def get_led_last_update(self, device_id):
        try:
            lastupdate=self._db.child('devices').child(device_id).child('leds').child('last_update').get()
            return lastupdate.val()
        except Exception as e:
            logger.error("Error getting time on firebase")
            return ""

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

    def get_my_devices(self):
        logger.debug(f"Retrieving devices that I am authorized to control.")
        self._my_device_ids = []
        devices = self._db.child('devices').get()
        for device in devices:
            if self._user['id'] in device.val()['device_info']['authorized_users']:
                self._my_device_ids.append(device.key())
        if len(self._my_device_ids) > 0:
            logger.debug(f"I am authorized to changed these devices: {self._my_device_ids}")
        else:
            logger.debug(f"I am not authorized to control any device at the moment.")

    def is_device(self):
        if self._device_info == {}:
            return False
        else:
            return True

    def remove_authorized_users(self,email):
        logger.debug(f"Removing user from authorized users: {email}")
        if self._device_info == {}:
            logger.info("Removing authorized users should be done from the raspberry pi with a registered device.")
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