# Automator
Automator is a program written in Python that lets you add key/mouse inputs then play them back. The inputs you currently add are key press/releases, mouse clicks, and mouse movement.

## How to run (with Python installed)
Run either one of these to install the required packages:

`pip install keyboard==0.13.5 mouse==0.7.1 PyQt5==5.15.7`

`pip install requirements.txt`

Now just run `python3 app.py`.

## How to run (without Python installed)
Go to [Releases](https://github.com/Androdir/Automator/releases/tag/automator) and download and extract `automator.zip`.

Open the new folder and open the folder "auto". Here, you will see another folder named "data" and an executable file named "app.exe". Run the file "app.exe".

P.S. app.exe was created with pyinstaller.

## How to use
When you run the program, you will see that you have 1 automation saved, "Auto Left Click". You can create new automations by clicking "Create New Automation". 

To select an automation, click on it in the "Automations" page.

When you select an automation, you will be sent to the second page, "Current Automation" where you can add/record inputs to the current automation.

In settings you will find settings like the keybind to start/stop the automation, automation loop iterations, loop speed (divides the length of pauses by the value)

To save your changes, either exit and click on "Save and exit", or press `CTRL + S`.
