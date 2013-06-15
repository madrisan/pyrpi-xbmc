import logging, os

homedir = os.path.expanduser('~')
videoPath = os.path.join(homedir, "Videos")
videoPathTmp = os.path.join(homedir, "Videos.tmp")

logfile = os.path.join(homedir, "xbmc-autoexec.log")
videocsvfile = os.path.join(homedir, "video-playlist.csv")
inifile = "/etc/sysconfig/rpi-xbmc"
