import math, netifaces, os

#
# Get the serial number of a RPi
#
def getserial():
    try:
        f = open('/proc/cpuinfo', 'r')
        for line in f:
            if line[0:6] == 'Serial':
                cpuserial = line[10:26]
        f.close()
    except:
        cpuserial = "ERROR00000000000"
    return cpuserial

#
# Change file timestamps of a file
#
def touch(fname, times=None):
    with file(fname, 'a'):
        os.utime(fname, times)

#
# Get the IP address of a given network interface
#
def getipaddr(ifaceName = 'eth0'):
    try:
        ifcfg = netifaces.ifaddresses(ifaceName)[netifaces.AF_INET][0]
    except:
        ifcfg = {'addr': None, 'netmask': None, 'broadcast': None}

    return ifcfg

#
# Return the system uptime
#
def uptime():
    uptime, idletime = [float(field) for field in open("/proc/uptime").read().split()]
    return math.trunc(uptime)

