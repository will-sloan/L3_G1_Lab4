# SYSC3010 Lab4
This repository was created for Lab4 of SYSC3010 course from Carleton University. The main goal is to use git as a Team, where each student changes files in their own branches and then merge their files in the main branch when new features are implemented.

# What does it do?
It allows ```users``` to remotely set the LED colors from the sense hat attached to a ```device``` (RPi).


## Deployment diagram
<p align="center" width="100%">
   <img src="https://github.com/roger-selzler/SYSC3010Lab4/blob/main/images/deployment_diagram.png" width="80%" margin-left="auto" margin-right="auto">
</p>

## The scripts
### The [backend.py](backend.py)
The [backend.py](backend.py) script has the ```Lab4db()``` class, which contains all the operations related to the database. For example: setting up users, devices, and configurations, as well as setting up the LED colors. It uses the configuration file (```mydbconfig.py```) to set and get values from the firebase database.

### The [device.py](device.py)
The [device.py](device.py) script should be executed on your Raspberry pi. It also needs the database and user configuration file (```mydbconfig.py```). When you execute the script for the first time, the device and user will be set in the database, and the LED display will be set with starting RGB colors.

The next time you execute the script, it will get the color values for the LED display from the database and set the sense hat LED display accordingly. While the script is running, it will *listen* for changes in the database by using [firebase streams](https://github.com/nhorvath/Pyrebase4#streaming). In other words, whenever a user changes the LED color using the GUI then a message is received by the stream and the pixel is updated accordingly.

## Authorizing users to control your sense hat LED display
Registered users in the database can be authorized to control your sense hat LED display. In fact, you should give your group mates authorization to control your device. You can achieve this by creating a file with the code below (with their respective emails).
```
from backend import Lab4db
from mydbconfig import *
db = Lab4db(config, email, firstname, lastname)

# Add each of your group mates
db.add_authorized_users('my_group_mate1_email@cmail.carleton.ca' )
db.add_authorized_users('my_group_mate2_email@cmail.carleton.ca' )

```
## The [frontend.py](frontend.py)
The [frontend.py](frontend.py) script can be run on your own computer and is responsible to provide a GUI implemented using [dash](https://dash.plotly.com/). It also needs the database and user configuration file (```mydbconfig.py```). When you execute the [frontend.py](frontend.py) file, a [flask](https://flask.palletsprojects.com/en/2.0.x/) server runs in the background. So the GUI can be accessed from your local network through the address ```<frontend_ip>:8050```, where ```frontend_ip``` is the ip of the device where the [frontend.py](frontend.py) is being executed. It can be run at the same RPi as the [device.py](device.py) script, or on your own computer.

Once you know the **IP address** of the device where you are running the [frontend.py](frontend.py) script, you can access it through your local network by typing the URL (```<frontend_ip>:8050```) in a web browser (from your smartphone, or computer, or through the web browser of your RPi, ...).  This is how it will look like if accessed from your smartphone:

<p align="center" width="100%">
   <img src="https://github.com/roger-selzler/SYSC3010Lab4/blob/main/images/lab4_frontend_sample.png" width="40%" margin-left="auto" margin-right="auto">
</p>


Note that the GUI can be run from any computer and can change the LED colors of any device that the user with authorization. The idea of this project is that any one of your teammates can change the sense hat pixels of your RPi.

# Install
There are packages required for this code to work. You can install them manually (look at the [install.sh](install.sh) script) or just execute it on a terminal from your RPi:
```
./install.sh
```


# Config
To use the Firebase database, you need to setup a Firebase database as performed in Lab3. 
Considering that the database is up and running, you need to provide the configuration for the database, and for each user. A sample file can be found in [here](dbconfig.py). You should then copy the file
```
cp dbconfig.py mydbconfig.py
``` 
and edit its contents. The file should contain:
1. Your ```email```
2. Your ```firstname```
3. Your ```lastname```
4. The firebase configuration ```config```

> These variables are used by many files and should be set for things to work properly.

The ```mydbconfig.py``` file should not be included in the repository since it has sensitive information about user and database. In addition, each student will have in common the config variable (database configuration), but the user information should be different for each student. To avoid pushing the file to your remote repository, just include the file in the ```.gitignore``` file. If you dont have the file, you should create the file and add one line for each ignored file. You can even ignore other directories and patterns in files. For example, the ```__pycache__``` should not be included in your repository. Your ```.gitignore``` file will look like this:
```
mydbconfig.py
*__pycache__*
```

# Deliverables

## Student #1
1. Fork the repository, **make it private, add your TA, the prof and your classmates**
2. Add collaborators (your group mates)

## Each student

### Setup
#### Step 1
Create your ```mydbconfig.py``` file.

Include

Once the database is setup and the mydbconfig.py is set, each student should run the [device.py](device.py) so that their device is registered on the database.

The device (RPi) will be registed under the user configuration. But, each student should give authorization to their groupmates to control his device. You can do that by running these commands in python from your RPi:


### GitHub and git tasks
1. Open at least 3 issues and assign a label to it
2. Self-assign 3 issues
3. Create a new branch to work on the assigned issues
4. Commit your changes to your current branch
5. Once the code reflect the solutions, merge with the main branch and resolve the issue.

### Issues
1. Capability to erase all LEDs.
   - Add a function in the [device.py](device.py) script to continuously check the joystick and set all the values of the LEDs to ```[0,0,0]```.
     - Inside this newly created function you should call (```clear_led()```) from the Lab4db to clear all LEDs. **NOT** calling the ```sense.set_pixels(...)```  function (otherwise the database will not be updated).
2. Add image samples
   - Take nice screenshots from your group mates LED screen and add to the [images](images) folder.
3. Update header value
    - Update the ```header``` value from the [frontend.py](frontend.py) script to be your session and group instead of ```SYSC3010 - Lab4```.
