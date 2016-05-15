#!/bin/sh

# execution on HOST

GUEST_IP=172.30.128.4

FW_rule_active=`sudo ipfw list | grep 00115`
FW_rule="00115 allow tcp from 172.30.128.0/24 to me"

# Update the user's cached credentials, validate
sudo -v

# check virtual box module is loaded
vbox_load=`kldstat | grep vboxdrv`
if [ "$vbox_load" == "" ] ; then
  sudo /home/vic/scripts/freebsd/load-vbox_moduls.sh
fi

if [ "$FW_rule" == "$FW_rule_active" ] ; then
  echo "rulle exist"
else
  sudo ipfw add "$FW_rule"
fi

# below code for skype pipe from linux to bsd
# allow access to X server from host
# xhost +$GUEST_IP


# TODO: check how to kill - /usr/local/bin/pulseaudio --start --log-target=syslog

# pulseaudio --check && pulseaudio -k
# pulseaudio --start
# activate USB earphones
# pactl set-default-sink oss_output.dsp6
# pactl set-default-source oss_input.dsp6


exit 0
