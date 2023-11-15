# NITC2.1
A newer version with refactored and organised code and error checking/input validation

Basically I saw a need for a simplified, easy to use Non-Incident Time Capture (NITC) process.

This allows members to add NITC entries on the go and as required, directly into beacon. Given the Title is not reportable, there is a fixed title that is just "NITC" and the date. One NITC entry is created for each person checking in, then out. It relies on the member logging time against the activity that they are undertaking for the reporting to be accurate. Activity tags need to be selected before checking out. It is possible to log against multiple tags. 

At the moment there are a few activities set up as shortcuts, with the whole list of available NITC tags selectable under the shortcut icons. As we move into Storm and Fire season I'll update it with more support role shortcuts as well (OOA, assist other emergency service etc) as well. 

I'm not a coder, so please forgive any poor implementations or dodgy code. I'm open to suggestions and if you'd like to contribute please get in touch.

As it's a FLASK application (Python web app) , you'll need to host accordingly.

To install you'll also need to install https://github.com/NSWSESMembers/pybeacon/archive/refs/heads/main.zip as well as the various librarys located in `requirements.txt`. If you have `pip` installed, you can easily install them all with `pip install -r requirements.txt` You'll also need to modify `NITC/config.py` to put in some details (SECRET KEY, USERNAME, PASSWORD)
