Synopsis
--------

_ptt-timer_ is a push-to-talk countdown timer on a Raspberry Pi with a Mini
PiTFT display. See the comments in
[ptt-timer.py](https://github.com/4hams/ptt-timer/blob/main/ptt-timer.py) for
all the details.

Motivation
----------

Some VHF/UHF amateur radio repeaters have a timeout to limit the length of a
transmission. This timer monitors the push-to-talk switch, showing a countdown
in seconds from the selected timeout value. This is to let the operator know
when its time to drop the transmission, in order to avoid triggering the
repeater timeout.

Usage
------------

Connect the push-to-talk line and ground to the Raspberry Pi, as described in
the comments. Connect the display. Optionally connect a passive buzzer. Follow
the instructions in the comments to install the required python modules. That
should be done in a virtual environment. Then run ptt-timer.py using Python.
Exit if desired by interrupting with a control-C.

Once proper operation is verified, the script can be initiated on boot by
putting it in crontab, or creating a systemd service for it. Then this timer
can be used headless and ssh-less. The Raspberry Pi should be given wireless
access to the internet for clock setting and synchronization.

Test
----

When running, verify that the local date, local time, and UTC time are shown
on the display.

Press the top button to toggle the sound between on and off, holding it down
momentarily to see the new state on the display. Press the bottom button to
cycle between timeout values, holding it down momentarily to see the new value.

Press the push-to-talk switch to start a countdown timer. Let it run to the end
to see the blinking display and hear the sound, if it's turned on and a buzzer
is installed.

License
-------

This code is under the zlib license, found in the source file.
