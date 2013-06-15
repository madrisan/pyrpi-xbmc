import os, psutil, sys, time
import xbmc
from cStringIO import StringIO

import rpi.iniparser, rpi.system, rpi.web

rpiserial = rpi.system.getserial()
url_rpsync = rpi.iniparser.getvar('rpsync', 'URL_RPSYNC_MONITORING')

#  ID    Name              Unit
# -----------------------------------
#  01    UPTIME            s
#  05    LOAD1             float
#  06    LOAD5             float
#  07    LOAD15            float
#  08    RAM               Use %
#  09    SWAP              Use %
#  10    ROOTFS            Use %
#  12    CPU-HEAT          C
#  15    ETH0-RX           b/s
#  16    ETH0-TX           b/s
#  20    UPDATE            0=ok, 1=ko
#  50    VIDEOFILE         0=ok, 1=download-failed, 2=md5-missing, 3=md5-does-not-match
#  55    XBMC-KEEPALIVE    0=ok, 1=ko

monitor_table = {
  # Name             ID      Unit
  # ----------------------------------
    'UPTIME'      :  '01',   # s
    'LOAD1'       :  '05',   # float
    'LOAD5'       :  '06',   # float
    'LOAD15'      :  '07',   # float
    'RAM'         :  '08',   # Use %
    'SWAP'        :  '09',   # Use %
    'ROOTFS'      :  '10',   # Use %
    'TEMP_C'      :  '12',   # C (warning: >= 60, critical: >= 80)
    'CPU_FREQ'    :  '13',   # MHza
    'VIDEO_FILE'  :  '30',   # 0=ok, 1=download-failed, 2=md5-missing, 3=md5-does-not-match
    'VIDEO_EXEC'  :  '31'    # bool
}

def url_wrapper(logger, monitor_id, monitoring_value):
    URL_MONITORING = "%s?nserial=%s&monitor=%s&value=%s" % (
        url_rpsync, rpiserial, monitor_table[monitor_id], monitoring_value)

    logger.debug("Sending monitoring info ({0}): {1}".format(monitor_id, URL_MONITORING))

    sys.stdout = result = StringIO()
    rpi.web.download(URL_MONITORING, "<stdout>")
    sys.stdout = sys.__stdout__

def check_uptime(logger):
    url_wrapper(logger, 'UPTIME', rpi.system.uptime())

def check_loadavg(logger):
    monitor_id = [ 'LOAD1', 'LOAD5', 'LOAD15' ]
    loadavg = os.getloadavg()
    for n in range(3):
        url_wrapper(logger, monitor_id[n], "{0:.2f}".format(loadavg[n]))

def check_memory(logger):
    url_wrapper(logger, 'RAM', "{0:.2f}".format(psutil.virtual_memory().percent))
    url_wrapper(logger, 'SWAP', "{0:.2f}".format(psutil.swap_memory().percent))

def check_filesystem(logger):
    url_wrapper(logger, 'ROOTFS', "{0:.2f}".format(psutil.disk_usage('/').percent))

def check_video(logger, video_error_id):
    errorcode = {
       'OK'                :   'O',
       'DOWNLOAD_FAILED'   :   '1',
       'MD5_MISSING'       :   '2',
       'MD5_DOES_NOT_MATCH':   '3'
    }

    try:
        url_wrapper(logger, 'VIDEO_FILE', errorcode[video_error_id])
    except:
        logger.error("BUG: That was no valid errocode (check_video:VIDEO_FILE): '%s'", video_error_id)

def check_temperature(logger):
    try:
        with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
            current_temp = f.read()
        degrees_c = (float(current_temp) / 1000)
    except:
        degrees_c = 0

    url_wrapper(logger, 'TEMP_C', "{0:.2f}".format(degrees_c))

def check_cpu_frequency(logger):
    try:
        with open("/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq", 'r') as f:
            cpu_cur_freq = f.read()
        cpu_cur_freq = (float(cpu_cur_freq) / 1000)
    except:
        cpu_cur_freq = 0

    url_wrapper(logger, 'CPU_FREQ', "{0:.0f}".format(cpu_cur_freq))

def check_video_execution(logger):
    is_playing_video = xbmc.Player().isPlayingVideo()
    url_wrapper(logger, 'VIDEO_EXEC', is_playing_video)
 
def alltasks(logger):
    check_uptime(logger)
    check_loadavg(logger)
    check_memory(logger)
    check_filesystem(logger)
    check_temperature(logger)
    check_cpu_frequency(logger)
    check_video_execution(logger)

