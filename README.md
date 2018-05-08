# Stratosphere Probe

As a term project with Bachelor students, we are preparing the launch of a unmanned probe that shall be lifted to the stratosphere by a commercial weather balloon. The probe is based on a Raspberry Pi A+ and we aim at the following features:

* Continuous APRS transmission of position, system status, and sensor data
* SSTV image transmission
* HD video recording

The project page (in German) is at http://www.ebusiness-unibw.org/wiki/Teaching/PS/2016

Note to self: When running from /etc/rc.local, you must make sure that the PATH includes all custom libraries etc.:

See https://stackoverflow.com/questions/13811575/python-scripts-issue-no-module-named-when-starting-in-rc-local

export PATH="$PATH::/usr/lib/python2.7:/usr/lib/python2.7/plat-arm-linux-gnueabihf:/usr/lib/python2.7/lib-tk:/usr/lib/python2.7/lib-old:/usr/lib/python2.7/lib-dynload:/usr/local/lib/python2.7/dist-packages:/usr/local/lib/python2.7/dist-packages/Adafruit_GPIO-1.0.3-py2.7.egg:/usr/local/lib/python2.7/dist-packages/Adafruit_PureIO-0.2.1-py2.7.egg:/usr/local/lib/python2.7/dist-packages/Adafruit_HTU21D-1.0.0-py2.7.egg:/usr/local/lib/python2.7/dist-packages/Adafruit_ADS1x15-1.0.2-py2.7.egg:/usr/lib/python2.7/dist-packages:/usr/lib/python2.7/dist-packages/gtk-2.0"
