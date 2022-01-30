# SYSC3010 Lab4
This repository was created for Lab4 of SYSC3010 course from Carleton University. The main goal is to use git as a Team, where each student changes files in their own branches and then merge their files in the main branch when new features are implemented.

# Install
To install the packages required in this lab, execute the [install.sh](install.sh) file on a terminal from the RPi using
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

# Hardware
One of the objectives of this lab is also adding new hardware to the RPi and sense hat. There is a mistake in the circuit provided that needs fixing. Only the png image of the circuit is provided. Students are required to provide the circuit file and update the figure with the correct connections.

![ External button to upload pressure values from sense hat ](images/external_button.png)

# Deliverables

## Student #1
1. Fork the repository, **make it private, add your TA, the prof and your classmates**
2. Add collaborators (your group mates)

## Each student

### Setup
Once the database is setup and the mydbconfig.py is set, each student should run the (device.py)[device.py] so that their device is registered on the database.

The device (RPi) will be registed under the user configuration. But, each student should give authorization to their groupmates to control his device. You can do that by running these commands in python from your RPi:
```
from backend import Lab4db
from mydbconfig import *
db = Lab4db(config, email, firstname, lastname)

# Add each of your group mates
db.add_authorized_users('my_group_mate_email@cmail.carleton.ca' )
```

### GitHub and git tasks
1. Open at least 3 issues and assign a label to it
2. Self-assign 3 issues
3. Create a new branch to work on the assigned issues
4. Commit your changes to your current branch
5. Once the code reflect the solutions, merge with the main branch and resolve the issue.

### Issues
1. Create the schematic circuit using Fritzing and upload it to the [hardware](hardware) folder.
2. Upload the updated [schematic image of the external button](images/external_button.png).
3. Edit the function ```upload_pressure()``` to upload pressure data once the button is pressed in the (device.py)[device.py] file.
4. Edit the function ```update_graph()``` to update the figure every 5 seconds in the (frontend.py)[frontend.py] script.
5. Edit the function ```get_pressure_data()``` to retrieve the pressure points from the database  in the (backend.py)[backend.py] script.
6. Edit the function ```set_pressure_data()``` to upload the pressure data to the database.
7. Modify the README.md file to describe what this projects does, including nice images.
8. Take nice screenshots from the project and add to the [images](images) folder.
