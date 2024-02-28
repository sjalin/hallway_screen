# hallway_screen
Application for E-ink screen in hallway

# How to get it working
Rename config_example.py to config.py and insert good values

# Install 
## Install packages 
```
sudo apt install tmux git python3-venv libopenblas-dev libopenjp2-7 python3-dev
```
## Make venv for python
```
python3 -m venv venv
```
## Activate venc
```
source venv/bin/activate
```
### Windows if testing the program there: 
```
venv\Scripts\activate
```
## Install python requirements:
```
pip3 install --upgrade pip setuptools wheel
pip3 install -r requirements.txt
pip3 install -r requirements_pi.txt # Only on raspberry pi
git submoduile init
git submodule update
```

## Make own config file
```
cp config_example.py config.py
```
Change values in config.py to fit your needs

## Ensure that the timezone is Stockholm
```
date
```
if not correct time enter raspberry pi setup wizard
```
raspi-config
```

## Turn on SPI in setup wizard
```
raspi-config
```

## Run at start-up
### Make startup script
Make a file `tmux_start.sh` with the following
```
#!/bin/bash
/usr/bin/tmux new-session -d -s hallway_screen
/usr/bin/tmux set-option -t hallway_screen remain-on-exit on
/usr/bin/tmux send-keys -t hallway_screen 'touch tralalalalala' Enter
/usr/bin/tmux send-keys -t hallway_screen 'cd hallway_screen' Enter
/usr/bin/tmux send-keys -t hallway_screen 'source venv/bin/activate' Enter
/usr/bin/tmux send-keys -t hallway_screen 'python3 main.py' Enter
```
### Add autostart to crontab
Add the following to crontab
```
@reboot /home/USER/tmux_start.sh
```
by running 
```
crontab -e
```