#! /usr/bin/env python
# -*- coding: utf-8 -*-

import subprocess
import socket
import threading
import os
import time

from onestroketest import OneStrokeTest




class MobileCloud:

    # 获取当前主机连接的移动设备信息的方法
    def get_device_info(self):
        port = 5000
        bp_port = 8000
        infos = []
        devices = subprocess.check_output('adb devices').decode().strip().split('\r\n')
        for i in range(1, len(devices)):
            device_name = devices[i].split('\t')[0].strip()
            platform_version = subprocess.check_output(
                'adb -s %s shell getprop ro.build.version.release' % device_name).decode().strip()
            port = self.find_port(port)
            bp_port = self.find_port(bp_port)
            infos.append((device_name, platform_version, port, bp_port))
            port += 1
            bp_port += 1
        return infos

    # 定义一个查找可用的端口的方法。
    def find_port(self, port):
        while self.check_port(port):
            port += 1
        return port

    # 定义一个检查传入端口是否占用的方法
    def check_port(self, port):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect(('127.0.0.1', port))
            s.shutdown(socket.SHUT_RDWR)
            return True
        except socket.error:
            return False

    # 构造appium server的启动命令
    # appium -a 127.0.0.1 -p 5000 -bp 6000 --device-name emulator-5554 --platform-version 4.4.2
    # --log XXX.log --log-level info --log-timestamp
    def start_appium(self, device_name, platform_version, port, bp_port):
        log_path = os.path.join(os.getcwd(), 'report/%s_appium.log' % device_name)
        cmd = 'appium -a 127.0.0.1 -p %d -bp %d --device-name %s --platform-version %s' \
              ' --log %s --log-level info --log-timestamp' % (port, bp_port, device_name, platform_version, log_path)
        os.system(cmd)


if __name__ == '__main__':
    mc = MobileCloud()
    devices = mc.get_device_info()
    threads = []
    for i in range(len(devices)):
        ost = OneStrokeTest(devices[i][0], devices[i][1], devices[i][2])
        server_thread = threading.Thread(target=mc.start_appium, args=(*devices[i],), name='server-%d' % i)
        client_thread = threading.Thread(target=ost.start_test, name='client-%d' % i)
        threads.append(server_thread)
        threads.append(client_thread)
    # 现在的线程顺序是 server-0, client-0, server-1, client-1, ..., server-n, client-n
    # 期望的线程顺序是 server-0, server-1, ..., server-n, client-0, client-1, ..., client-n
    # def sorted(t):
    #     return t.getName()[0: 1]
    threads.sort(key=lambda t: t.getName()[0: 1], reverse=True)
    for t in threads:
        if t.getName() == 'client-0':
            time.sleep(30)
        # 设置守护线程
        t.setDaemon(True)
        t.start()
    for t in threads:
        if t.getName().startswith('client'):
            t.join()
    os.system('taskkill /f /im node.exe')
    print('********** 全部测试完成 ************')
