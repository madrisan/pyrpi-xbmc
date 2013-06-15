import netifaces, os, socket, sys, urllib2

from cStringIO import StringIO
from os.path import basename
from urlparse import urlsplit

import rpi.iniparser, rpi.system

def url2name(url):
    return basename(urlsplit(url)[2])

#
# Return the content of a text file
#
def getfilecontents(filename):
    with open(filename) as f:
        return f.read()

#
# download the URL "url" and (optionally) save the result to 'userFileName'
#
def download(url, userFileName = None):
    try:
        u = urllib2.urlopen(url, None, 900)
    except urllib2.HTTPError, e:
        return "HTTPError <%s>" % e.code
    except urllib2.URLError, e:
        return "URLError <%s>" % e.args
    except socket.timeout:
        return "Socket timeout"
    except:
        return "Unexpected error: ", sys.exc_info()[0]

    meta = u.info()

    if userFileName:
        fileName = userFileName
    else:
        fileName = url2name(url)
        if meta.has_key('Content-Disposition'):
            # If the response has Content-Disposition, we take file name from it
            fileName = u.info()['Content-Disposition'].split('filename=')[1].strip("\"'")
        elif u.url != url: 
            # If we were redirected, the real file name we take from the final URL
            fileName = url2name(u.url)

    filesize = int(meta.getheaders("Content-Length")[0])

    if fileName == "<stdout>":
        sys.stdout.write(u.read())
    else:
        f = open(fileName, 'wb')
        filesize_dl = 0
        block_sz = 8192

        while True:
            try:
                buffer = u.read(block_sz)
                if not buffer: break
            except socket.timeout:
                return "Socket timeout"

            filesize_dl += len(buffer)

            try:
                f.write(buffer)
            except IOError, e:
                return "IOError: %s" % e.code

            #status = r"%10d  [%3.2f%%]" % (filesize_dl, filesize_dl * 100. / filesize)
            #status = status + chr(8)*(len(status)+1)
            #print status

        f.close()

def registration():
    registration_status = {
        "0" : "RPi successfully registred",
        "1" : "RPi registration failure",
        "2" : "RPi already registered" }

    for ifaceName in ['eth0', 'wlan0']:
        ipaddr = rpi.system.getipaddr(ifaceName)['addr']
        if ipaddr:
            URL_REGISTER = "%s?nrpi=%s&nserial=%s&ipaddr=%s&Submit=Confirmer" % (
                rpi.iniparser.getvar('rpsync', 'URL_RPSYNC_REGISTER'),
                socket.gethostname(), rpi.system.getserial(),
                ipaddr)

            sys.stdout = result = StringIO()
            download(URL_REGISTER, "<stdout>")
            sys.stdout = sys.__stdout__

            try:
                return registration_status[result.getvalue()]
            except:
                return "BUG: the web application returned an unknown retcode"
        else:
            return "ERROR: neither eth0 nor wlan0 has an IP address"

def getvideolist(filename = None):
    URL_VIDEOCSV = "%s?serial=%s" % (
      rpi.iniparser.getvar('rpsync', 'URL_RPSYNC_GETCSV'),
      rpi.system.getserial())

    download_status = {
        0 : "OK",
        1 : "serial number not found",
        2 : "no association S/N-folder",
        3 : "missing parameter",
        4 : "CSV file not found" }

    download(URL_VIDEOCSV, filename)

    statinfo = os.stat(filename)
    if (statinfo.st_size == 1):
        retcode = getfilecontents(filename)
        try:
            return download_status[int(retcode)]
        except:
            return "BUG: the web application returned an unexpected retcode"

