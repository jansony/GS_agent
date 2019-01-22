#!/usr/bin/python
# -*- coding:gb2312 -*-

import os, sys, socket, datetime
import time, threading, re
import MySQLdb

#改下控制台标题
VERSION = "v1.0.7 2018-04-28"
os.system("title 运维守护工具 " + VERSION + "  " + sys.argv[0])

#以下内容不常修改
#==============================================================================

#数据信息，一般后续常修改，用于访问后台配置的各个区的开服时间，用于开新区
g_DBConfig = {
    'user' : 'root',
    'pass' : '0987abc123',
}

#监听端口
SERVER_BIND_PORT = 8000

MAX_SLOT = len(os.listdir('D:\GameServer'))


if MAX_SLOT == 25:
    
    #需要扫描的区槽数量
    MAX_USE_SLOT_COUNT = 20

    #部署的最大区槽数量
    MAX_SLOT_COUNT = 25
elif MAX_SLOT == 30:
    #需要扫描的区槽数量
    MAX_USE_SLOT_COUNT = 30

    #部署的最大区槽数量
    MAX_SLOT_COUNT = 30

g_sSlotDir = r'D:\GameServer\slot_%d'
g_sDBServerConfigFile = r'D:\GameServer\slot_%d\dbserver\DBServer.txt'
g_sGameWorldConfigFile = r'D:\GameServer\slot_%d\gameworld\GameWorld.txt'
g_sOpenTimeConfigFile = r'D:\GameServer\slot_%d\gameworld\runtime\opentime.txt'
g_sServerHaveOpend = r'D:\GameServer\slot_%d\gameworld\startok.txt'
    
g_sServerMerged = r'D:\GameServer\slot_%d\merged.txt'    
    
g_sRSFFileName = r'D:\GameServer\slot_%d\gameworld\rsf.txt'
 
g_sGameWorldExeFile = r'D:\GameServer\slot_%d\gameworld\GameWorld64_debug.exe' 
 

#HTML协议头
g_ResponseHeaders = '''
HTTP/1.0 200 OK
Content-Type: text/html; charset=gbk
Content-Length: %d

%s
'''


#==============================================================================
#通用函数
#==============================================================================
def printLog( sLog ):
    sTimeAndLog = "[{}]{}".format(time.strftime('%Y-%m-%d %H:%M:%S'), sLog)
    print sTimeAndLog
    #写入日志文件，方便后续查问题
    f = file('run.log', 'a') 
    f.write(sTimeAndLog + '\n') 
    f.close() 
     
#获取配置中某个配置项的值 （字符串型）
#例如：  Host = "10.11.2.15",  --数据库服务器地址     
#正确情况返回  10.11.2.15  这个文本(即默认替换掉双引号)
#而      Port = 3306,  返回   3306
def getConfigValue(sLine):
    sLine = sLine.strip() #去除首尾空格
    #找到逗号 , 并截取它之前的内容
    nPos = sLine.find(',')
    if nPos > -1:
        sLine = sLine[:nPos]
    sLine = sLine.split("=")[1] #截取等号后面的内容
    sLine = sLine.strip() #去除首尾空格
    sRet = sLine.replace( '"', '' ) #去除可能存在的双引号
    return sRet
    
#检测某个端口是否可用（即能否绑定在该端口上）
#如果可用返回 True   否则返回False
def IsPortEnable(nPort):
    bResult = False
    listenSocket = socket.socket()
    try:
        listenSocket.bind(('', nPort))
        bResult = True
    except BaseException, e:
        print '%d Bind Port except:' % nPort, e
    finally:
        listenSocket.close() 
        
    return bResult
     
#SVN更新
def UpdateSvnPath():
    sResult = ""
    OutPutMsg = os.popen("svn_update.bat")
    sResult += OutPutMsg.read()       
        
    #把返回结果的换号加上<br>，方便浏览器显示
    sResult = sResult.replace( "\n", "<br>" ) 
    return sResult
    
#热更新脚本指令的函数(它用临时的线程来跑，不阻塞返回)
#它会每分钟写一个rsf.txt文件到运行中的区槽中去
def SlotRsfProc():
    f = os.popen("wmic process get ExecutablePath")
    AllAppExecutablePath = f.read()
    f.close() 
    try:
        for i in range(1, MAX_SLOT_COUNT + 1):
            if (g_sGameWorldExeFile % i) in AllAppExecutablePath:  #程序在允许才有必要更新
                printLog("区槽%d 写入热更新文件标记" % i )
                f = file((g_sRSFFileName % i), 'w') #以写入的方式打开文件
                f.close() #关闭文件
                time.sleep(30) #暂停60秒
    except BaseException, e:
        print 'except:', e
 
#响应中心服发过来的热更新指令
def SlotRsf():
    sResult = "OK! 已启动热更新脚本线程"
    threading.Thread(target=SlotRsfProc, args=()).start()
    time.sleep(1) #返回太快会报错？！！！ 坑。。。
    return sResult
    
#区槽更新补丁（通常是该服务器上的所有区都同时更新，特殊的混杂不同spid的只能手动去选择性更新！）
def SlotUpdatePatch():
    sFromDir = r'D:\temp\slot' #补丁目录（注意！！ 不要带 \ 符号)
    #同步SVN
    sResult = UpdateSvnPath()   
    #拷贝补丁
    nSucceed = 0
    nFailure = 0
    if 'gameworld' in os.listdir(sFromDir):
        for i in range(1, MAX_SLOT_COUNT + 1):
            sTemp = g_sSlotDir % i
            sCommand = 'xcopy %s %s /E /V /I /R /K /X /Y' % ( sFromDir, sTemp )
            ret = os.system( sCommand )
            if ret == 0:
                nSucceed += 1  
            else:
                nFailure += 1
                print '目录更新失败！ %s' % (sTemp)
    else:
        nFailure += 1 
        print '不存在gameworld目录,请注意检查!!'
    # for i in range(1, MAX_SLOT_COUNT + 1):
        # sTemp = g_sSlotDir % i
        # sCommand = 'xcopy %s %s /E /V /I /R /K /X /Y' % ( sFromDir, sTemp )
        # ret = os.system( sCommand )
        # if ret == 0:
            # nSucceed += 1  
        # else:
            # nFailure += 1
            # print '目录更新失败！ %s' % (sTemp) 
    sResult += '<br>执行结果： %d 成功,  %d 失败<br>' % (nSucceed, nFailure)
    now = time.localtime()
    print '\n执行结果： %d 成功,  %d 失败' % (nSucceed, nFailure),'{}_{}_{} {}:{}:{}'.format(now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min, now.tm_sec)
    # print '\n执行结果： %d 成功,  %d 失败' % (nSucceed, nFailure)
    return sResult
    
#获取区槽的版本号（这个用于查看每次版本更新情况）
def GetSlotVersion():
    sResult = ""
    for i in range(1, MAX_SLOT_COUNT + 1):  #查看补丁要检查整个25个区槽的情况，不单单是前20个区，因为25区以后做模版使用
        sTemp = '区槽%d：'% i
        sSlotPath = g_sSlotDir % i
        if os.path.exists(sSlotPath):
            sVersionFile = os.path.join(sSlotPath, 'version.txt')
            if os.path.isfile(sVersionFile):
                sTemp += time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getmtime(sVersionFile))) + '<br>'
            else:
                sTemp += '未知' + '<br>'
        else:
            sTemp += '未知' + '<br>'
            
        sResult += sTemp
        
    return sResult
    
    
#获取区槽的端口占用信息（用于查询某个待开区的端口是否已经被别的进程占用！）
def GetSlotPortInfo():
    sResult = ""
    
    #如果有nginx运行说明该服务器是https代理，则不用检测94xx 的端口
    bUseNginx = False
    nGateWayPort = 9400
    f = os.popen('wmic process where name="%s" get name' % 'nginx.exe')
    txt = f.read()
    f.close()
    if txt.find('nginx.exe') > -1:
        bUseNginx = True
        nGateWayPort = 9500
        print "本区采用https代理，不检测94XX系列端口"
        
    for i in range(1, MAX_USE_SLOT_COUNT + 1):
        if not os.path.isfile(g_sOpenTimeConfigFile % i): #如果还是待开区才需要检测
            sResult += "======================================================================<br>区槽%d: " % i + '<br>'
            nPort = nGateWayPort + i  #网关端口
            if IsPortEnable(nPort): #说明端口被占用
                sResult += '<font style="color:rgb(0,162,0)">网关端口： %d 可用</font>' % nPort + '<br>'
            else:
                sResult += '<font style="color:rgb(255,0,0)">网关端口： %d 已被占用</font>' % nPort + '<br>'
            
            nPort = 6400 + i  #逻辑端口
            if IsPortEnable(nPort): #说明端口被占用
                sResult += '<font style="color:rgb(0,162,0)">逻辑端口： %d 可用</font>' % nPort + '<br>'
            else:
                sResult += '<font style="color:rgb(255,0,0)">逻辑端口： %d 已被占用</font>' % nPort + '<br>'
                
            nPort = 5400 + i  #DB端口
            if IsPortEnable(nPort): #说明端口被占用
                sResult += '<font style="color:rgb(0,162,0)">DB端口： %d 可用</font>' % nPort + '<br>'
            else:
                sResult += '<font style="color:rgb(255,0,0)">DB端口： %d 已被占用</font>' % nPort + '<br>'
                
            nPort = 7400 + i  #日志端口
            if IsPortEnable(nPort): #说明端口被占用
                sResult += '<font style="color:rgb(0,162,0)">日志端口： %d 可用</font>' % nPort + '<br>'
            else:
                sResult += '<font style="color:rgb(255,0,0)">日志端口： %d 已被占用</font>' % nPort + '<br>'

    
    return sResult
    
#获取本游戏服的部署情况
def GetSlotInfo(bAllInfo):
    sResult = ''
    f = os.popen("wmic process get ExecutablePath")
    AllAppExecutablePath = f.read()
    f.close() 
    #扫描当前服务器的所有游戏区，看看都有哪些数据库
    for i in range(1, MAX_USE_SLOT_COUNT + 1):  
        sTemp = '位置%d：'% i
        if os.path.exists(g_sSlotDir % i):  #区槽目录不存在直接跳过
            sOpenTime = '待开服'
            if os.path.isfile(g_sServerMerged % i): 
                sOpenTime = '<font style="color:rgb(255,128,0)">已被合服</font>'
            elif os.path.isfile(g_sOpenTimeConfigFile % i): #如果该区有开服时间文件，则说明是已开服 
                sOpenTime = '<font style="color:rgb(0,162,0)">已开服</font>'
  
            #sLastStartTime = ' '
            sRunning = '<font style="color:rgb(255,0,0)">未运行</font>'
            if ((g_sGameWorldExeFile % i) in AllAppExecutablePath): #如果该区有运行标志，并且进程存在
                if os.path.isfile(g_sServerHaveOpend % i):
                    sRunning = '<font style="color:rgb(0,162,0)">运行中OK</font>'
                else:
                    sRunning = '<font style="color:rgb(255,128,0)">进程运行中但启动异常</font>'
                #sLastStartTime += os.path.getmtime(g_sServerHaveOpend % i).strftime('%Y-%m-%d %H:%M:%S')
            
            nServerIndex = 0
            sSQLHost = '未知'
            sDBName = '未知'
            SPID = '未知'
            nPort = 9400 + i    #理论对应的对外端口
            
            #读取服务器id  (不能在里面读取数据库信息，因为有全局数据库在里面，这种读取的方式会出现问题的！)
            sFileName = g_sGameWorldConfigFile % i
            if os.path.isfile(sFileName):
                f = file(sFileName) #如果不填模式，默认是 'r' 读的模式
                while True:
                    line = f.readline() # 读入每一行
                    if len(line) == 0: #即便是换行空行都是有值的，为0这里表示文件结尾
                        break
                        
                    line = line.strip()
                    if 'ServerIndex' in line:
                        tmp = getConfigValue(line)
                        try:
                            nServerIndex = int(tmp)
                        except BaseException, e:
                            printLog( '区槽%d 的服务器id解析异常！'  % i) 
                            print 'except:', e
                    elif 'SPID' in line:
                        SPID = getConfigValue(line)
                     
                f.close()
            #读取数据库信息    
            sFileName = g_sDBServerConfigFile % i
            if os.path.isfile(sFileName):    
                f = file(sFileName) #如果不填模式，默认是 'r' 读的模式
                while True:
                    line = f.readline() # 读入每一行
                    if len(line) == 0: #即便是换行空行都是有值的，为0这里表示文件结尾
                        break
                        
                    line = line.strip()
                    if 'Host' in line:
                        sSQLHost = getConfigValue(line)
                    elif 'DBName' in line:
                        sDBName = getConfigValue(line)
                        
                f.close()
            
            if bAllInfo: #比较详细的信息
                sTemp += sOpenTime + '|' + sRunning + '|' + str(nServerIndex) + '区|' + sSQLHost + '|' + sDBName + '|' + SPID + '|' + str(nPort) + '|' + '<br>'
            else: #简单信息
                sTemp += sOpenTime + '|' + sRunning + '|' + str(nServerIndex) + '区|' + SPID + '|' + '<br>'
                
        else:
            sTemp += '区槽目录不存在'
        
        sResult += sTemp
        
    return sResult                
    
#根据指定区槽的数据库配置信息去读取该数据库中是否有启动指令
def checkStartServerApp(sSlotStartScript, nServerIndex, sSQLHost, sDBName):
    global g_DBConfig
    
    boNeedStartServer = False
    
    con = MySQLdb.connect(host = sSQLHost, user = g_DBConfig['user'], passwd = g_DBConfig['pass'], db = sDBName, port = 3306)      
    cur = con.cursor()
    cur.execute( "select id, serverid, cmd from servercmd limit 1" )
    con.commit()
    rets = cur.fetchall()            
    
    if len(rets) > 0:
        rec = rets[0]
        id = rec[0]
        serverid = rec[1]
        cmd = rec[2]
        print id, serverid, cmd
        if cmd == 'start_server': #暂时只处理这个指令类型
            if (serverid == nServerIndex):
                cur.execute( "delete from `servercmd` where id = %d" % id )
                con.commit()
                
                printLog("检测到启动服务器指令！启动的是 serverid = %d" % nServerIndex )
                #启动程序
                os.system( 'start ' + sSlotStartScript)
            else:
                printLog("启动服务器指令异常！ 服务器id不一致！期望启动的是 nServerIndex = %d, 后台却是 serverid = %d , " % (nServerIndex, serverid) )
                 
    cur.close()
    con.close() 

    
def start_script(script_path):
    print script_path
    os.system('start %s' % script_path)
    TXT = 'OK!'
    return TXT
 
#==============================================================================
# 功能1： 处理中心服发来的各种操作请求的线程处理函数  （例如svn更新，热更新指令等等）
#==============================================================================
def tcplink(sock, addr):
    try:
        data = sock.recv(4096)
        #print('收到数据内容:%s' % data)
        boNeedRestart = False
        sData = "error" #默认是错误的内容
        pos = data.find('HTTP/')
        if pos != -1:
            cmd = data[5: pos - 1] #提取出请求的文件名
            if 'svn_update' == cmd:
                sData = UpdateSvnPath()
                boNeedRestart = True
            elif 'ping' == cmd:  #返回版本信息，运行状态
                sData = 'Running OK!  VERSION = ' + VERSION
            elif 'get_slot_info' == cmd: #获取本游戏服的部署情况(详细信息，给运维用的)
                sData = GetSlotInfo(True)
            elif 'get_server_running' == cmd: #获取本游戏服的部署情况(简单信息，给运营用的)
                sData = GetSlotInfo(False)
            elif 'get_slot_version' == cmd: #获取区槽的版本号（这个用于查看每次版本更新情况）
                sData = GetSlotVersion()
            elif 'get_slot_port_info' == cmd: #获取区槽的端口占用信息（用于查询某个待开区的端口是否已经被别的进程占用！）
                sData = GetSlotPortInfo()
            elif 'slot_update_patch' == cmd: #区槽更新补丁（通常是该服务器上的所有区都同时更新，特殊的混杂不同spid的只能手动去选择性更新！）
                sData = SlotUpdatePatch()
            elif 'slot_rsf' == cmd: #热更新区槽    
                sData = SlotRsf()
            elif 'stop_slots' == cmd:# 更新前关闭正在运行的区槽
                sData = start_script(r'D:\tools\command\区槽的停止和开启\stop_slot.py')
            elif 'start_slots' == cmd:# 更新后启动更新前关闭的区槽
                sData = start_script(r'D:\tools\command\区槽的停止和开启\start_slot.py')
            elif 'start_process_moniter' == cmd:
                sData = start_script(r'D:\tools\command\重启进程监控\重启进程监控.py')
            elif 'record_runing_slots' == cmd:
                sData = start_script(r'D:\tools\command\区槽的停止和开启\记录当前运行的区槽.py')
            elif 'start_log_gate_db' == cmd:
                sData = start_script(r'D:\tools\command\启动log_db_gateway三个进程\start_log_gate_db.py')
                
        #回复客户端
        sock.sendall(g_ResponseHeaders % ( len(sData), sData))
        sock.close()
        
        #需要重启自身脚本
        if boNeedRestart:
            printLog("更新重启自身脚本")
            time.sleep(1)
            os.system("restart.bat")
            os._exit(0)
            
    except BaseException, e: #把所有的异常都捕获
        sock.close()
        print '客户端异常:', e

        
#==============================================================================
# 功能2： 处理运营开服的指令的监听检测线程函数  
#==============================================================================     
def checkStartServerAppThreadProc():
    sSlotStartScript = r'D:\GameServer\slot_%d\open_new_server.py'
    while True:
        #扫描当前服务器的所有游戏区，看看都有哪些数据库
        for i in range(1, MAX_USE_SLOT_COUNT + 1):  
            if not os.path.exists(g_sSlotDir % i):  #区槽目录不存在直接跳过
                continue
            if os.path.isfile(g_sServerHaveOpend % i): #如果该区有运行标志，则说明是已开服，不用进行后续的检测
                continue
            if os.path.isfile(g_sOpenTimeConfigFile % i): #如果该区有开服时间文件，则说明是已开服，不用进行后续的检测
                continue
            
            nServerIndex = 0
            sSQLHost = ''
            sDBName = ''
            
            #读取服务器id  (不能在里面读取数据库信息，因为有全局数据库在里面，这种读取的方式会出现问题的！)
            sFileName = g_sGameWorldConfigFile % i
            if os.path.isfile(sFileName):
                f = file(sFileName) #如果不填模式，默认是 'r' 读的模式
                while True:
                    line = f.readline() # 读入每一行
                    if len(line) == 0: #即便是换行空行都是有值的，为0这里表示文件结尾
                        break
                        
                    line = line.strip()
                    if 'ServerIndex' in line:
                        str = getConfigValue(line)
                        try:
                            nServerIndex = int(str)
                        except BaseException, e:
                            printLog( '区槽%d 的服务器id解析异常！'  % i) 
                            print 'except:', e
                        
                f.close()
            #读取数据库信息    
            sFileName = g_sDBServerConfigFile % i
            if os.path.isfile(sFileName):    
                f = file(sFileName) #如果不填模式，默认是 'r' 读的模式
                while True:
                    line = f.readline() # 读入每一行
                    if len(line) == 0: #即便是换行空行都是有值的，为0这里表示文件结尾
                        break
                        
                    line = line.strip()
                    if 'Host' in line:
                        sSQLHost = getConfigValue(line)
                    elif 'DBName' in line:
                        sDBName = getConfigValue(line)
                        
                f.close()
                
            #如果都能正常解析到指定区槽的数据库信息，那么可以开始尝试扫描数据库
            if (nServerIndex > 0) and (nServerIndex < 5000) and (len(sSQLHost) > 0) and (len(sDBName) > 0):
                #开始尝试读取后台指令
                try:
                    #printLog( '正在监听 区槽%d 的服务器数据库启动指令！'  % i) 
                    checkStartServerApp(sSlotStartScript%i, nServerIndex, sSQLHost, sDBName)
                except BaseException, e:
                    printLog( '区槽%d 的服务器数据库监听检测异常！'  % i) 
                    print 'except:', e
            else:
                if (nServerIndex < 5000):
                    printLog( '解析区槽%d的数据库信息异常' % i )
                    print nServerIndex
                    print sSQLHost
                    print sDBName
                
        time.sleep(30)  #每半分钟执行一次检测是否有开启指令    
        #调试
        #printLog( '正在监听等待运营开启新区事件...' )
              
def main():
    
    #检测是否需要启动新区的线程
    threading.Thread(target=checkStartServerAppThreadProc, args=()).start()
    
    print "监听端口：%d" % SERVER_BIND_PORT
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('0.0.0.0', SERVER_BIND_PORT))
    s.listen(5)

    while True:
        sock, addr = s.accept() # 接受一个新连接:
        t = threading.Thread(target=tcplink, args=(sock, addr)) # 创建新线程来处理TCP连接:
        t.start()
        
try:
    main()   
except BaseException, e: #把所有的异常都捕获
    print '程序发生异常:', e


#raw_input('\n\n\n程序执行完毕，按任意键退出...') 

