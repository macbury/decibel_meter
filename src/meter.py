#!/usr/bin/python
import time
import json
from boot import CONFIG, LOGGER
from mqtt import MqttClient
import alsaaudio, time, audioop

# Open the device in nonblocking capture mode. The last argument could
# just as well have been zero for blocking mode. Then we could have
# left out the sleep call in the bottom of the loop
inp = alsaaudio.PCM(alsaaudio.PCM_CAPTURE,alsaaudio.PCM_NONBLOCK)

# Set attributes: Mono, 8000 Hz, 16 bit little endian samples
inp.setchannels(2)
inp.setrate(16000)
inp.setformat(alsaaudio.PCM_FORMAT_S16_LE)

# The period size controls the internal number of frames per period.
# The significance of this parameter is documented in the ALSA api.
# For our purposes, it is suficcient to know that reads from the device
# will return this many frames. Each frame being 2 bytes long.
# This means that the reads below will return either 320 bytes of data
# or 0 bytes of data. The latter is possible because we are in nonblocking
# mode.
inp.setperiodsize(160)

MAX_SAMPLE = 32768.0

sum = 0.0
samples = 0

mqtt = MqttClient(CONFIG['mqtt'])
def onConnect(mqtt):
  LOGGER.info("connected!")

mqtt.onConnect = onConnect
mqtt.start()

state_topic = CONFIG['meter']['state_topic']

while True:
  # Read data from device
  l, data = inp.read()
  if l:
    # Return the maximum of the absolute value of all samples in a fragment.
    power = audioop.max(data, 2) / MAX_SAMPLE
    sum += power
    samples += 1
  time.sleep(.001)

  if samples >= 60:
    power = round((sum / samples) * 100)
    print "Current power: {}".format(power)
    mqtt.publish(state_topic, power)
    samples = 0
    sum = 0
