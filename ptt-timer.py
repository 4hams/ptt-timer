'''
  ptt-timer.py -- push-to-talk countdown timer
  Copyright (C) 2025 Mark Adler
  Version 1.0  9 Mar 2025  Mark Adler

  This software is provided 'as-is', without any express or implied
  warranty.  In no event will the author be held liable for any damages
  arising from the use of this software.

  Permission is granted to anyone to use this software for any purpose,
  including commercial applications, and to alter it and redistribute it
  freely, subject to the following restrictions:

  1. The origin of this software must not be misrepresented; you must not
     claim that you wrote the original software. If you use this software
     in a product, an acknowledgment in the product documentation would be
     appreciated but is not required.
  2. Altered source versions must be plainly marked as such, and must not be
     misrepresented as being the original software.
  3. This notice may not be removed or altered from any source distribution.

  Mark Adler
  madler@alumni.caltech.edu
'''

# Provide a push-to-talk countdown timer on a Raspberry Pi with a Mini PiTFT
# 135x240 display ($10 at https://www.adafruit.com/product/4393). Also show the
# date, local time, and UTC time on the display. Permit the choice of different
# countdown durations, and whether to provide an audio alert, using the buttons
# on the display. This would be used with a repeater that has a timeout.

# The PTT line is connected to GPIO26, header pin 37, and the radio ground is
# connected to the RPi ground, e.g. to the neighboring header pin 39. This
# works nicely with a Raspberry Pi Zero 2W ($18 w/header). WiFi is useful to
# set and synchronize the date and time with an NTP server. The PTT signal can
# come from the microphone connector, or a data jack if the radio has one.

# The bottom button will cycle between four timeout times: 90, 60, 30, and 15
# seconds. The new timeout time is displayed as long as the bottom button is
# pressed.

# A passive buzzer can optionally be connected across GPIO21, pin 40, and
# ground, pin 34 ($7 for ten of them: https://www.amazon.com/dp/B01MR1A4NV,
# with header connectors). It will buzz on and off in the last five seconds.
# The top button will cycle between the sound on and off. The new sound state
# is shown as long as the top button remains pressed. Initially the sound is
# off.

# This can be run on a headless Raspberry Pi, and set up to run on boot by
# putting the command "@reboot python3 ptt-timer.py" in your crontab (using
# crontab -e). Both "python3" and "ptt-timer.py" would be replaced by the full
# path names for those, where python3 would refer to the link in the virtual
# environment where the modules were installed, and ptt-timer.py would refer to
# its location in the file system.

# Follow the instructions on these pages to install the required modules:
#
# https://learn.adafruit.com/circuitpython-on-raspberrypi-linux/installing-circuitpython-on-raspberry-pi
# https://learn.adafruit.com/adafruit-mini-pitft-135x240-color-tft-add-on-for-raspberry-pi/python-setup

import time
from datetime import datetime
import signal
import board
import digitalio
import pwmio
from adafruit_rgb_display import st7789
from PIL import Image, ImageDraw, ImageFont

# Catch a shutdown to turn off the display. Otherwise it stays on with the last
# content so long as there is power, even after the shutdown completes!
def sigterm(*_):
    raise(KeyboardInterrupt)
signal.signal(signal.SIGTERM, sigterm)

# Setup the ST7789 display.
disp = st7789.ST7789(
    board.SPI(),
    digitalio.DigitalInOut(board.D25),
    digitalio.DigitalInOut(board.CE0),
    None, 135, 240, 64000000,
    x_offset = 53, y_offset = 40)

# Create an image buffer for drawing. Swap width and height for landscape view.
width = disp.height
height = disp.width
rotation = 90
image = Image.new("RGB", (width, height))
draw = ImageDraw.Draw(image)

# Basic colors.
black = (0, 0, 0)
red = (255, 0, 0)
green = (0, 255, 0)
blue = (0, 0, 255)
cyan = (0, 255, 255)
magenta = (255, 0, 255)
yellow = (255, 255, 0)
white = (255, 255, 255)

# Draw and display a black box to clear the image. Turn on the backlight.
draw.rectangle((0, 0, width, height), fill=black)
disp.image(image, rotation)
back = digitalio.DigitalInOut(board.D22)
back.switch_to_output()
back.value = True

# Medium and large fonts to use.
med = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 48)

# Connect up the GPIO pins. GPIO26 is the PTT switch, with the other end of the
# switch connected to ground. GPIO19 is an output set high, which sources 3.3V
# through a 47K resistor connected to GPIO26 (PTT). The push-to-talk switch
# then pulls down GPIO26 when pushed. push is False if the PTT switch is open.
# Otherwise it is the time the PTT switch was closed. These are the three
# inside pins on the end of the header, opposite the display. (Note: GPIO19 and
# the resistor are just for demonstrating with no radio. They are not needed
# when connected to a radio, which provides its own pull-up resistor and
# voltage. In that case, the three pullup lines below can be commented out.)
pullup = digitalio.DigitalInOut(board.D19)
pullup.switch_to_output()
pullup.value = True
ptt = digitalio.DigitalInOut(board.D26)
ptt.switch_to_input()
push = False if ptt.value else time.time()

# Connect up the buttons. button.value is true if the button is up and false if
# the button is down (go figure). The top button cycles between the sound on
# and off. The bottom button cycles through the timeout values.
top = digitalio.DigitalInOut(board.D23)
top.switch_to_input()
toggle = not top.value
bot = digitalio.DigitalInOut(board.D24)
bot.switch_to_input()
cycle = not bot.value

# Cycle of timeout values when pressing button B. Set initial timeout to 90.
# The timeout value blinks and a buzzer buzzes in the last warn seconds.
step = {90 : 60, 60 : 30, 30 : 15, 15 : 90}
timeout = next(iter(step))
warn = 5

# Set up the buzzer. Default to no audio alert. The top button will cycle
# between the sound enabled and disabled.
sound = False
buzzer = pwmio.PWMOut(board.D21, frequency = 262, duty_cycle = 0)

try:
    # Do this forever, until interrupted with a ^C, or there is an error.
    while True:
        # Put the current date, local time, and UTC time in the image buffer.
        draw.rectangle((0, 0, width, height), fill=black)
        draw.text((0, -2), datetime.now().strftime("%B %d, %Y"),
                  font=med, fill=white)
        draw.text((0, 26), "LOC " + datetime.now().strftime("%a"),
                  font=med, fill=green)
        draw.text((108, 26), datetime.now().strftime("%H:%M:%S"),
                  font=med, fill=green)
        draw.text((0, 54), "UTC " + datetime.utcnow().strftime("%a"),
                  font=med, fill=yellow)
        draw.text((108, 54), datetime.utcnow().strftime("%H:%M:%S"),
                  font=med, fill=yellow)

        # Check the PTT switch. Check button B if the PTT switch is open. Check
        # button A if both PTT and B are open.
        if ptt.value:
            # The PTT switch is open.
            push = False
            buzzer.duty_cycle = 0
            if bot.value:
                # The bottom button is open.
                cycle = False
                if top.value:
                    # The top button is open.
                    toggle = False
                else:
                    # The top button is closed.
                    if not toggle:
                        # The top button closed just now.
                        sound = not sound
                    toggle = True
                    draw.text((0, 82), f"Sound {'on' if sound else 'off'}",
                              font=big, fill=cyan)
            else:
                # The bottom button is closed.
                if not cycle:
                    # The bottom button just closed -- cycle timeout.
                    timeout = step[timeout]
                    cycle = True
                # As long as the bottom button remains closed, show the new
                # timeout value.
                draw.text((0, 82), f"T/O {timeout} s", font=big, fill=red)
        else:
            # The PTT switch is closed.
            if not push:
                # The PTT just closed. Save the time this happened.
                push = time.time()
            left = timeout - time.time() + push
            # Show the time left, but blink when five seconds or less left.
            if left > warn or round(3 * left) % 2 == 0:
                buzzer.duty_cycle = 0
                draw.text((0, 82), f"  {left:.1f} s", font=big, fill=red)
            else:
                if sound:
                    # Turn the buzzer on and off in the last five seconds.
                    buzzer.duty_cycle = 32768

        # Copy the image buffer to the display.
        disp.image(image, rotation)

        # Update the display and check the switches ten times a second.
        time.sleep(0.1)

except KeyboardInterrupt:
    # Backup and overwrite the displayed interrupt character (^C).
    print("\r  \r", end="")

finally:
    # Exit cleanly, resetting the GPIO pins, blanking the screen, turning off
    # the backlight, and killing the buzzer.
    buzzer.deinit()
    bot.deinit()
    top.deinit()
    ptt.deinit()
    pullup.deinit()
    draw.rectangle((0, 0, width, height), fill=black)
    disp.image(image, rotation)
    back.value = False
