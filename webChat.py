# -*- coding: utf-8 -*-

import os
import string
import time
import socket
import requests as requests

############识别文字功能 start############
from paddleocr import PaddleOCR

def getScriptDir():
    return os.path.split(os.path.realpath(__file__))[0]

def getText(img_path):
    # Paddleocr目前支持的多语言语种可以通过修改lang参数进行切换
    # 例如`ch`, `en`, `fr`, `german`, `korean`, `japan`
    ocr = PaddleOCR(use_angle_cls=True, lang="ch", show_log = False)  # need to run only once to download and load model into memory
    result = ocr.ocr(img_path, cls=True)
    comments = []
    for line in result[0]:
        textOfThisLine:string = line[1][0]
        textOfThisLine = textOfThisLine.replace("：", ":")
        if(":" in textOfThisLine):
            nameAndComment = tuple(textOfThisLine.split(':', 1))
            comments.append(nameAndComment)
        
        if("来了" in textOfThisLine):
            nameAndComment = tuple(textOfThisLine.split('来了', 1))
            comments.append(nameAndComment)
    return comments
############识别文字功能 end############

############截图功能 start############
from ctypes import windll, byref, c_ubyte
from ctypes.wintypes import RECT, HWND
import numpy as np
import cv2

GetDC = windll.user32.GetDC
CreateCompatibleDC = windll.gdi32.CreateCompatibleDC
GetClientRect = windll.user32.GetClientRect
CreateCompatibleBitmap = windll.gdi32.CreateCompatibleBitmap
SelectObject = windll.gdi32.SelectObject
BitBlt = windll.gdi32.BitBlt
SRCCOPY = 0x00CC0020
GetBitmapBits = windll.gdi32.GetBitmapBits
DeleteObject = windll.gdi32.DeleteObject
ReleaseDC = windll.user32.ReleaseDC

windll.user32.SetProcessDPIAware()

def capture(handle: HWND):
    r = RECT()
    GetClientRect(handle, byref(r))
    width, height = r.right, r.bottom
    dc = GetDC(handle)
    cdc = CreateCompatibleDC(dc)
    bitmap = CreateCompatibleBitmap(dc, width, height)
    SelectObject(cdc, bitmap)
    BitBlt(cdc, 0, 0, width, height, dc, 0, 0, SRCCOPY)
    total_bytes = width*height*4
    buffer = bytearray(total_bytes)
    byte_array = c_ubyte*total_bytes
    GetBitmapBits(bitmap, total_bytes, byte_array.from_buffer(buffer))
    DeleteObject(bitmap)
    DeleteObject(cdc)
    ReleaseDC(handle, dc)

    return np.frombuffer(buffer, dtype=np.uint8).reshape(height, width, 4)

############截图功能 end############

def getScriptDir():
    return os.path.split(os.path.realpath(__file__))[0]

class Socket():
    def __init__(self):
        Address = ('127.0.0.1', 25565) # Socket服务器地址,根据自己情况修改
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.sock.connect(Address)  # 尝试连接服务端
        except Exception:
            print(time.strftime("[%Y-%m-%d %H:%M:%S]", time.localtime()) + ' [ERROR] 无法连接到Socket服务器,请检查服务器是否启动')

    def close(self):
        self.sock.close()

    def sendMsg(self, msg):
        try:
            self.sock.sendall(msg.encode()) # 尝试向服务端发送消息
        except Exception:
            print(time.strftime("[%Y-%m-%d %H:%M:%S]", time.localtime()) + ' [ERROR] 无法连接到Socket服务器,请检查服务器是否启动')

class Watcher():
    def __init__(self):
        self.monitoringFile = f'{getScriptDir()}/liveFile'
        self.commentlist = []

    def startWatcher(self):
        index = 1
        while True:
            handle = windll.user32.FindWindowW(None, "视频号直播")
            image = capture(handle)

            sp = image.shape            #获取图像形状：返回【行数值，列数值】列表
            sz1 = sp[0]                 #图像的高度（行 范围）rows
            sz2 = sp[1]                 #图像的宽度（列 范围）cols
            #sz3 = sp[2]                #像素值由【RGB】三原色组成
            
            a=int(417) # y start 这个数值按实际来写
            b=int(sz1) # y end
            c=int(1171) # x start 这个数值按实际来写
            d=int(sz2) # x end
            cropImg = image[a:b,c:d]   #裁剪图像
            try:
                cv2.imwrite(self.monitoringFile + '/' +str(index)+".jpg", cropImg)  #
            except Exception:
                print("cv2.imwrite func fail! 可能是未打开微信直播工具")
            files = os.listdir(self.monitoringFile)
            if files:
                for _ in files:
                    filepath = self.monitoringFile + '/' + _
                    messages = getText(filepath)

                    for message in messages:
                        userName = message[0]
                        comment = message[1]
                        if comment in self.commentlist:
                            continue
                        self.commentlist.append(comment)
                        msg = f"{userName}:{comment}"
                        # self.mySocket.sendMsg(msg)
                        print(msg)
                    try:
                        os.remove(filepath)
                    except PermissionError as e:
                        time.sleep(1)
                        os.remove(filepath)
            time.sleep(2)
            index += 1

if __name__ == '__main__':
    print("web chat running ...")
    if not os.path.isdir(getScriptDir()+"/liveFile"):
        os.makedirs(getScriptDir()+"/liveFile")
    watcher = Watcher()
    watcher.startWatcher()
