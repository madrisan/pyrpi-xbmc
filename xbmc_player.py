import csv, os, shutil, time
import datetime as dt
import xbmc, xbmcgui

import rpi.constants, rpi.hash, rpi.web

from rpi.constants import videoPath as videoPath
from rpi.constants import videoPathTmp as videoPathTmp
from rpi.constants import videocsvfile as videocsvfile
from rpi.constants import videocsvfile as videocsvfile
from rpi.monitoring import check_video

reload_PlayList = True

def init(logger):
    # if the RPi reboots with no network connectivity, the Video files
    # can have a date in far future, so touch them to avoid this problem
    if not os.path.exists(videoPath):
        os.mkdir(videoPath)
    dirList = os.listdir(videoPath)
    for fname in dirList:
        fnameWithPath = os.path.join(videoPath, fname)
        logger.debug("Touching %s", fnameWithPath)
        with file(fnameWithPath, 'a'): os.utime(fnameWithPath, None)

def videos(msg, logger, timeperiod):
    global reload_PlayList

    now = dt.datetime.now()
    ago = now - dt.timedelta(minutes = timeperiod)

    logger.debug("Creating the directory: %s...", videoPathTmp)
    if not os.path.exists(videoPathTmp):
        os.mkdir(videoPathTmp)

    logger.debug("Downloading the Video playlist (%s)...", videocsvfile)

    progress_perc = 0

    if (msg == 'job_multimedia-1st'):
        dialog = xbmcgui.DialogProgress()
        ret = dialog.create('Multimedia Files Updater',\
                            'Downloading the Video Playlist...')
        dialog.update(int(progress_perc))
        time.sleep(1)

    errorcode = rpi.web.getvideolist(videocsvfile)

    if (errorcode):
        logger.warning("Download of the Video Playlist failed: %s", errorcode)
    else:
        if (msg == 'job_multimedia-1st'):
            progress_perc += 5
            dialog.update(int(progress_perc), 'Downloading Video Files...')

        # get the number of lines of the CSV files
        csvfilerows = len(open(videocsvfile).readlines())
        progress_barunit = 95.0 / csvfilerows

        videocsvlist = []
        with open(videocsvfile, 'rb') as csvfile:
            data = csv.reader(csvfile, delimiter=';')
            logger.debug("The Video Playlist is %d line(s) long", csvfilerows)
            for (filename, md5sum, url) in data:
                if not md5sum:
                    logger.error("BUG missing MD5 hash for %s", url)

                videocsvlist.append(filename)
                checkfile = os.path.join(videoPath, filename)

                if (msg == 'job_multimedia-1st'):
                    dialog.update(int(progress_perc), 'Downloading Video Files...', filename)
                
                logger.debug("Looking for file: {0} (MD5:{1})".format(filename, md5sum))

                if (os.path.isfile(checkfile) and rpi.hash.md5match(checkfile, md5sum)):
                    logger.debug("Local copy (%s) is good", checkfile)
                    progress_perc += progress_barunit
                    if (msg == 'job_multimedia-1st'):
                        dialog.update(int(progress_perc), 'Downloading Video Files...',\
                                      "%s - skip" % filename)
                    time.sleep(1)
                else:
                    candidatefile = os.path.join(videoPathTmp, filename)

                    if (os.path.isfile(checkfile)):
                        logger.debug("Downloading (replace): %s", url)
                    else:
                        logger.debug("Downloading (new): %s", url)

                    errorcode = rpi.web.download(url, candidatefile)
                    if (errorcode):
                        logger.error("Download failed: %s", errorcode)
                        rpi.monitoring.check_video(logger, 'DOWNLOAD_FAILED')
                        logger.debug("Removing incomplete file (if any): %s", candidatefile)
                        try: os.remove(candidatefile)
                        except OSError: pass
                    else:
                        if not (rpi.hash.md5match(candidatefile, md5sum)):
                            logger.error("MD5 hash does not match: removing %s", candidatefile)
                            os.remove(candidatefile)
                            rpi.monitoring.check_video(logger, 'MD5_DOES_NOT_MATCH')
                        else:
                            logger.debug("Moving {0} to {1}".format(candidatefile, videoPath))
                            shutil.copy(candidatefile, videoPath)
                            os.remove(candidatefile)
                            rpi.monitoring.check_video(logger, 'OK')
                            logger.debug("Playlist need to be reloaded")
                            reload_PlayList = True
                    progress_perc += progress_barunit

        logger.debug("Video playlist: %s", videocsvlist)

        if (msg == 'job_multimedia-1st'):
            dialog.update(100)
            time.sleep(1)
            dialog.close()

        videoDirList = os.listdir(videoPath)
        for fvideo in videoDirList:
            # erase the Videos files not found in the playlist
            if not fvideo in videocsvlist:
                logger.debug("Removing old file: %s", fvideo)
                os.remove(os.path.join(videoPath, fvideo))
                reload_PlayList = True

    dirList = os.listdir(videoPath)

    if reload_PlayList == False:
        logger.debug("Checking for new files...")
        for fname in dirList:
            st = os.stat(os.path.join(videoPath, fname))
            mtime = dt.datetime.fromtimestamp(st.st_mtime)
            if mtime > ago:
                logger.debug(" - %s", fname)
                reload_PlayList = True

        logger.debug("Reload playlist: %s", reload_PlayList)

    if reload_PlayList:
        # create the playlist
        videoList = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
        videoList.clear()

        logger.info("Reloading the video playlist")

        for fname in sorted(dirList):
            fpath = os.path.join(videoPath, fname)
            videoList.add(fpath)
            logger.debug(" - %s", fname)

        xbmc.Player().showSubtitles(False)
        xbmc.Player().play(videoList)
        xbmc.executebuiltin('PlayerControl(RepeatAll)')
        reload_PlayList = False
    
