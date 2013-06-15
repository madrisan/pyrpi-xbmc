import netifaces, sched, threading, time
import xbmc
import rpi, rpi.iniparser, rpi.logger, rpi.monitoring, rpi.system, rpi.xbmc_player, rpi.web

logginglevel = rpi.iniparser.getvar('scheduler', 'loglevel')
logger = rpi.logger.newlogger(logginglevel)
logger.debug("New logger with loglevel set to %d", logginglevel)

# define the job(s) to be executed by the scheduler

joblist = [ 'multimedia', 'monitoring' ]
timeperiod_default = { 'multimedia': 60, 'monitoring': 10 }

# job for multimedia activities (XBMC)
def job_multimedia(msg):
    logger.debug("Executing new job: %s", msg)
    rpi.xbmc_player.videos(msg, logger, timeperiod['multimedia'])
    # re-register task to be run in 'timeperiod['multimedia']' minutes
    t = int(time.time() / 60 + timeperiod['multimedia']) * 60
    (scheduler['multimedia']).enterabs(t, 1, job_multimedia, ('job_multimedia-next',))

# job for monitoring the RPi
def job_monitoring(msg):
    #logger.debug("Executing new job: %s", msg)
    rpi.monitoring.alltasks(logger)
    # re-register task to be run in 'timeperiod['monitoring'] minutes
    t = int(time.time() / 60 + timeperiod['monitoring']) * 60
    (scheduler['monitoring']).enterabs(t, 1, job_monitoring, ('job_monitoring-next',))

job = { 'multimedia': job_multimedia, 'monitoring': job_monitoring }

scheduler = {}
timeperiod = {}
for jobname in joblist:
    # get user defined values from the configuration file
    inivar = rpi.iniparser.getvar('scheduler', 'timeperiod_' + jobname)
    try: inivar = int(inivar)
    except: inivar = timeperiod_default[jobname]
    timeperiod.update({jobname: inivar})
    logger.debug("Setting the timeperiod for {0} job to {1}".format(jobname, timeperiod[jobname]))
    # register the jobs
    scheduler.update({jobname: sched.scheduler(time.time, time.sleep)})

def run():
    # display the network IP address
    for ifaceName in ['eth0', 'wlan0']:
        ipaddr = rpi.system.getipaddr(ifaceName)['addr']
        netmask = rpi.system.getipaddr(ifaceName)['netmask']
        if ipaddr:
            logger.debug("Detected a network IP address: {1}/{2} ({0})".format(ifaceName, ipaddr, netmask))
            xbmc.executebuiltin('Notification(Network IP Address, ' + ifaceName + ': ' + ipaddr + ', 5000)')
            time.sleep(5)
            break

    logger.debug("Starting the job scheduler ...")
    xbmc.executebuiltin('Notification(Raspberry Pi Video Player, 10000)')

    logger.info("Trying to register the RPi with S/N %s ...", rpi.system.getserial())
    result = rpi.web.registration()
    logger.info("%s", result)

    rpi.xbmc_player.init(logger)

    # start the threads to run the first instances of the defined jobs
    for jobname in joblist:
        (scheduler[jobname]).enter(1, 1, job[jobname], ('job_%s-1st' % jobname,))
        thread = threading.Thread(target=(scheduler[jobname]).run)
        thread.start()

