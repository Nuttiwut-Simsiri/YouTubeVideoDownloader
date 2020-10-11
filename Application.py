import sys
from os import path
from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot, QTimer
from PyQt5.QtWidgets import (
    QApplication, 
    QMainWindow, 
    QPushButton, 
    QComboBox,
    QLineEdit,
    QFileDialog,
    QTextEdit,
)
from ui.pyScript.ui_yt_vd import Ui_MainWindow
from pytube import YouTube
from pytube.cli import on_progress
from pprint import pprint
from re import findall
import math

class SearchThread(QThread):
    streamSignal = pyqtSignal(list)
    ytObjectSignal = pyqtSignal(object)
    downloadInfo = pyqtSignal(str)

    def __init__(self, textEdit):
        super().__init__()
        self.url = ''
        self.waitFlg = 0
        self.textEdit = textEdit

    def setUrl(self, newurl):
        self.url = newurl
        self.waitFlg = 1

    def run(self):
        while 1:
            if self.waitFlg:
                yt = YouTube(self.url, on_progress_callback=self.showDownloadProgress)
                self.streamSignal.emit(yt.streams.filter(file_extension='mp4').all())
                self.ytObjectSignal.emit(yt)
                self.waitFlg = 0

            self.msleep(50)

    
    def setVideoSize(self, videoSize):
        self.videoSize = videoSize
    
    def showDownloadProgress(self, chunk: bytes, file_handler, bytes_remaining: int):
        percent = round(100 - ((100 * bytes_remaining)/self.videoSize),2)
        if percent%10 == 0:
            self.downloadInfo.emit(f'Downloading {percent}%')

class YouTubeVideoDownLoader(QMainWindow, Ui_MainWindow):

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.SAVE_PATH = path.abspath('./downloads')
        self.setupGUIConnect()
        

    def setupGUIConnect(self):
        self.searchBtn.clicked.connect(self.handleSearch)
        self.browseBtn.clicked.connect(self.getFolder)
        self.downloadBtn.clicked.connect(self.downloadVideo)
        self.searchTh = SearchThread(self.textEdit)
        self.searchTh.start()
        self.searchTh.streamSignal.connect(self.setComboBoxItems)
        self.searchTh.ytObjectSignal.connect(self.setYT)
        self.searchTh.downloadInfo.connect(self.setDownloadinfo)
        self.availableFormats = []


    @pyqtSlot(str)
    def setDownloadinfo(self, str):
        print(str)
        self.textEdit.setText(str)

    @pyqtSlot(object)
    def setYT(self, yt):
        self.yt = yt

    def handleSearch(self):
        self.availableFormats = []
        parsedURL = self.url.text().split('&')[0]
        self.searchTh.setUrl(parsedURL)
        
    def parseSteamTag(self, tag):
        result = {}
        tagObj = findall(r'\w+=.+"', tag)
        if tagObj:
            attributes = tagObj[0].split(" ")
            for attr in attributes: 
                tag_name, value = attr.split("=")
                result[tag_name] = value.replace('"','')
        return result

    @pyqtSlot(list)
    def setComboBoxItems(self, streams):
        for stream in streams:
            streamDict = self.parseSteamTag(str(stream))
            self.availableFormats.append(streamDict)
            if streamDict['type'] == 'video':
                self.available_format.addItem(f'Type: {streamDict["mime_type"]}, Video Resolution: {streamDict["res"]}, fps:{streamDict["fps"]}')
            else:
                self.available_format.addItem(f'Type: {streamDict["mime_type"]}, Audio Bitrate: {streamDict["abr"]}')

    
    def getFolder(self):
        folderName = QFileDialog.getExistingDirectory(
            self, 'Select a directory', self.SAVE_PATH)
        if folderName:
            self.savePath.setText(folderName)
        else:
            self.savePath.setText(self.SAVE_PATH)
    
    def sizeof_fmt(num, suffix='B'):
        magnitude = int(math.floor(math.log(num, 1024)))
        val = num / math.pow(1024, magnitude)
        if magnitude > 7:
            return '{:.1f}{}{}'.format(val, 'Yi', suffix)
        return '{:3.1f}{}{}'.format(val, ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi'][magnitude], suffix)

    def downloadVideo(self):
        if self.available_format:
            selIndex = self.available_format.currentIndex()
            videoInfo = self.availableFormats[selIndex]
            video = self.yt.streams.get_by_itag(videoInfo['itag'])
            try:
                videoTitle = video.title
                print(video.title, video.default_filename)
                self.searchTh.setVideoSize(int(video.filesize))
            except Exception as e:
                print(e)
                videoTitle = self.yt.title
                self.searchTh.setVideoSize(1)
                
            path = self.savePath.text()
            print('\nDownloading--- '+videoTitle+' into location : '+path)
            self.textEdit.setText('\nDownloading--- '+videoTitle+' into location : '+path)
            QTimer.singleShot(0, lambda: video.download(output_path=path, filename=f'{videoTitle}-{videoInfo["res"]}.{videoInfo["fps"]}'))


if __name__ == "__main__":
    QApplication = QApplication(sys.argv)
    yt_vd = YouTubeVideoDownLoader()
    yt_vd.show()
    sys.exit(QApplication.exec_()) 