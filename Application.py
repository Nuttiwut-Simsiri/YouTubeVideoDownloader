from os.path import join
import sys
from os import path
from PyQt5 import uic
from PyQt5.QtWidgets import (
    QApplication, 
    QMainWindow, 
    QPushButton, 
    QComboBox,
    QLineEdit,
    QFileDialog,
    QTextEdit,
)

import win32clipboard
from pytube import YouTube
from pytube.cli import on_progress
from pprint import pprint
from re import findall
import math

class YouTubeVideoDownLoader(QMainWindow):

    def __init__(self):
        super().__init__()
        self.uic = uic.loadUi(path.abspath('ui/yt-vd.ui'), self)
        self.SAVE_PATH = path.abspath('./downloads')
        self.init_ui()
        

    def init_ui(self):
        self.searchButton = self.findChild(QPushButton, 'searchBtn')
        self.searchButton.clicked.connect(self.onClickSearchVideo)
        self.urlInput = self.findChild(QLineEdit, 'url')
        self.availableFormatMenu = self.findChild(QComboBox, 'available_format') 
        self.browseButton = self.findChild(QPushButton, 'browseBtn')
        self.browseButton.clicked.connect(self.getFolder)
        self.saveFolder = self.findChild(QLineEdit, 'savePath')
        self.saveFolder.setText(self.SAVE_PATH)
        self.downloadButton = self.findChild(QPushButton, 'donloadBtn')
        self.downloadButton.clicked.connect(self.downloadVideo)
        self.donwloadInfo = self.findChild(QTextEdit, 'textEdit')

    def parseSteamTag(self, tag):
        result = {}
        tagObj = findall(r'\w+=.+"', tag)
        if tagObj:
            attributes = tagObj[0].split(" ")
            for attr in attributes: 
                tag_name, value = attr.split("=")
                result[tag_name] = value.replace('"','')
        return result

    def createComboBoxItem(self, streams):
        for stream in streams:
            streamDict = self.parseSteamTag(str(stream))
            print(streamDict)
            self.availableFormats.append(streamDict)
            if streamDict['type'] == 'video':
                self.availableFormatMenu.addItem(f'Type: {streamDict["mime_type"]}, Video Resolution: {streamDict["res"]}, fps:{streamDict["fps"]}')
            else:
                self.availableFormatMenu.addItem(f'Type: {streamDict["mime_type"]}, Audio Bitrate: {streamDict["abr"]}')

    
    def getFolder(self):
        folderName = QFileDialog.getExistingDirectory(
            self, 'Select a directory', self.SAVE_PATH)
        if folderName:
            self.saveFolder.setText(folderName)
        else:
            self.saveFolder.setText(self.SAVE_PATH)

    def onClickSearchVideo(self):
        try:
            self.availableFormats = []
            self.yt = YouTube(self.urlInput.text(),  on_progress_callback=self.showDownloadProgress)
            print('Title :', self.yt.title)
            print('Views :', self.yt.views)
            print('Length :', self.yt.length)

            self.createComboBoxItem(self.yt.streams.filter(progressive=True).all())
        except Exception as e: 
            print("Error",e) #to handle exception 
            input('Hit Enter to exit')
            exit(0)
    
    def sizeof_fmt(num, suffix='B'):
        magnitude = int(math.floor(math.log(num, 1024)))
        val = num / math.pow(1024, magnitude)
        if magnitude > 7:
            return '{:.1f}{}{}'.format(val, 'Yi', suffix)
        return '{:3.1f}{}{}'.format(val, ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi'][magnitude], suffix)


    def showDownloadProgress(self, chunk: bytes, file_handler, bytes_remaining: int):
        percent = round(100 - ((100 * bytes_remaining)/self.videoSize),2)
        print(f'Downloading {percent}%')
        self.donwloadInfo.setText(f'Downloading {percent}%')


    def downloadVideo(self):
        if self.availableFormatMenu:
            selIndex = self.availableFormatMenu.currentIndex()
            videoInfo = self.availableFormats[selIndex]
            video = self.yt.streams.get_by_itag(videoInfo['itag'])
            try:
                videoTitle = video.title
                print(video.title, video.default_filename)
                self.videoSize = int(video.filesize)
            except Exception as e:
                print(e)
                videoTitle = self.yt.title
                self.videoSize = 1
                
            path = self.saveFolder.text()
            print('\nDownloading--- '+videoTitle+' into location : '+path)
            self.donwloadInfo.setText('\nDownloading--- '+videoTitle+' into location : '+path)
            video.download(output_path=path, filename=f'{videoTitle}-{videoInfo["res"]}.{videoInfo["fps"]}')


if __name__ == "__main__":
    QApplication = QApplication(sys.argv)
    yt_vd = YouTubeVideoDownLoader()
    yt_vd.show()
    sys.exit(QApplication.exec_()) 