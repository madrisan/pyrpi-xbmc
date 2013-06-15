import ConfigParser
from rpi.constants import inifile as inifile

def getvar(section, option):
    config = ConfigParser.ConfigParser()
    try:
        config.read(inifile)
    except:
        return None

    if (config.has_section(section) and
        config.has_option(section, option)):
        return config.get(section, option)
