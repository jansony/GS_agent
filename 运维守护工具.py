#!/usr/bin/python
# -*- coding:gb2312 -*-

import os, sys, socket, datetime
import time, threading, re
import MySQLdb

#���¿���̨����
VERSION = "v1.0.7 2018-04-28"
os.system("title ��ά�ػ����� " + VERSION + "  " + sys.argv[0])

#�������ݲ����޸�
#==============================================================================

#������Ϣ��һ��������޸ģ����ڷ��ʺ�̨���õĸ������Ŀ���ʱ�䣬���ڿ�����
g_DBConfig = {
    'user' : 'root',
    'pass' : '0987abc123',
}

#�����˿�
SERVER_BIND_PORT = 8000

MAX_SLOT = len(os.listdir('D:\GameServer'))


if MAX_SLOT == 25:
    
    #��Ҫɨ�����������
    MAX_USE_SLOT_COUNT = 20

    #����������������
    MAX_SLOT_COUNT = 25
elif MAX_SLOT == 30:
    #��Ҫɨ�����������
    MAX_USE_SLOT_COUNT = 30

    #����������������
    MAX_SLOT_COUNT = 30

g_sSlotDir = r'D:\GameServer\slot_%d'
g_sDBServerConfigFile = r'D:\GameServer\slot_%d\dbserver\DBServer.txt'
g_sGameWorldConfigFile = r'D:\GameServer\slot_%d\gameworld\GameWorld.txt'
g_sOpenTimeConfigFile = r'D:\GameServer\slot_%d\gameworld\runtime\opentime.txt'
g_sServerHaveOpend = r'D:\GameServer\slot_%d\gameworld\startok.txt'
    
g_sServerMerged = r'D:\GameServer\slot_%d\merged.txt'    
    
g_sRSFFileName = r'D:\GameServer\slot_%d\gameworld\rsf.txt'
 
g_sGameWorldExeFile = r'D:\GameServer\slot_%d\gameworld\GameWorld64_debug.exe' 
 

#HTMLЭ��ͷ
g_ResponseHeaders = '''
HTTP/1.0 200 OK
Content-Type: text/html; charset=gbk
Content-Length: %d

%s
'''


#==============================================================================
#ͨ�ú���
#==============================================================================
def printLog( sLog ):
    sTimeAndLog = "[{}]{}".format(time.strftime('%Y-%m-%d %H:%M:%S'), sLog)
    print sTimeAndLog
    #д����־�ļ����������������
    f = file('run.log', 'a') 
    f.write(sTimeAndLog + '\n') 
    f.close() 
     
#��ȡ������ĳ���������ֵ ���ַ����ͣ�
#���磺  Host = "10.11.2.15",  --���ݿ��������ַ     
#��ȷ�������  10.11.2.15  ����ı�(��Ĭ���滻��˫����)
#��      Port = 3306,  ����   3306
def getConfigValue(sLine):
    sLine = sLine.strip() #ȥ����β�ո�
    #�ҵ����� , ����ȡ��֮ǰ������
    nPos = sLine.find(',')
    if nPos > -1:
        sLine = sLine[:nPos]
    sLine = sLine.split("=")[1] #��ȡ�Ⱥź��������
    sLine = sLine.strip() #ȥ����β�ո�
    sRet = sLine.replace( '"', '' ) #ȥ�����ܴ��ڵ�˫����
    return sRet
    
#���ĳ���˿��Ƿ���ã����ܷ���ڸö˿��ϣ�
#������÷��� True   ���򷵻�False
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
     
#SVN����
def UpdateSvnPath():
    sResult = ""
    OutPutMsg = os.popen("svn_update.bat")
    sResult += OutPutMsg.read()       
        
    #�ѷ��ؽ���Ļ��ż���<br>�������������ʾ
    sResult = sResult.replace( "\n", "<br>" ) 
    return sResult
    
#�ȸ��½ű�ָ��ĺ���(������ʱ���߳����ܣ�����������)
#����ÿ����дһ��rsf.txt�ļ��������е�������ȥ
def SlotRsfProc():
    f = os.popen("wmic process get ExecutablePath")
    AllAppExecutablePath = f.read()
    f.close() 
    try:
        for i in range(1, MAX_SLOT_COUNT + 1):
            if (g_sGameWorldExeFile % i) in AllAppExecutablePath:  #������������б�Ҫ����
                printLog("����%d д���ȸ����ļ����" % i )
                f = file((g_sRSFFileName % i), 'w') #��д��ķ�ʽ���ļ�
                f.close() #�ر��ļ�
                time.sleep(30) #��ͣ60��
    except BaseException, e:
        print 'except:', e
 
#��Ӧ���ķ����������ȸ���ָ��
def SlotRsf():
    sResult = "OK! �������ȸ��½ű��߳�"
    threading.Thread(target=SlotRsfProc, args=()).start()
    time.sleep(1) #����̫��ᱨ�������� �ӡ�����
    return sResult
    
#���۸��²�����ͨ���Ǹ÷������ϵ���������ͬʱ���£�����Ļ��Ӳ�ͬspid��ֻ���ֶ�ȥѡ���Ը��£���
def SlotUpdatePatch():
    sFromDir = r'D:\temp\slot' #����Ŀ¼��ע�⣡�� ��Ҫ�� \ ����)
    #ͬ��SVN
    sResult = UpdateSvnPath()   
    #��������
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
                print 'Ŀ¼����ʧ�ܣ� %s' % (sTemp)
    else:
        nFailure += 1 
        print '������gameworldĿ¼,��ע����!!'
    # for i in range(1, MAX_SLOT_COUNT + 1):
        # sTemp = g_sSlotDir % i
        # sCommand = 'xcopy %s %s /E /V /I /R /K /X /Y' % ( sFromDir, sTemp )
        # ret = os.system( sCommand )
        # if ret == 0:
            # nSucceed += 1  
        # else:
            # nFailure += 1
            # print 'Ŀ¼����ʧ�ܣ� %s' % (sTemp) 
    sResult += '<br>ִ�н���� %d �ɹ�,  %d ʧ��<br>' % (nSucceed, nFailure)
    now = time.localtime()
    print '\nִ�н���� %d �ɹ�,  %d ʧ��' % (nSucceed, nFailure),'{}_{}_{} {}:{}:{}'.format(now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min, now.tm_sec)
    # print '\nִ�н���� %d �ɹ�,  %d ʧ��' % (nSucceed, nFailure)
    return sResult
    
#��ȡ���۵İ汾�ţ�������ڲ鿴ÿ�ΰ汾���������
def GetSlotVersion():
    sResult = ""
    for i in range(1, MAX_SLOT_COUNT + 1):  #�鿴����Ҫ�������25�����۵��������������ǰ20��������Ϊ25���Ժ���ģ��ʹ��
        sTemp = '����%d��'% i
        sSlotPath = g_sSlotDir % i
        if os.path.exists(sSlotPath):
            sVersionFile = os.path.join(sSlotPath, 'version.txt')
            if os.path.isfile(sVersionFile):
                sTemp += time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getmtime(sVersionFile))) + '<br>'
            else:
                sTemp += 'δ֪' + '<br>'
        else:
            sTemp += 'δ֪' + '<br>'
            
        sResult += sTemp
        
    return sResult
    
    
#��ȡ���۵Ķ˿�ռ����Ϣ�����ڲ�ѯĳ���������Ķ˿��Ƿ��Ѿ�����Ľ���ռ�ã���
def GetSlotPortInfo():
    sResult = ""
    
    #�����nginx����˵���÷�������https�������ü��94xx �Ķ˿�
    bUseNginx = False
    nGateWayPort = 9400
    f = os.popen('wmic process where name="%s" get name' % 'nginx.exe')
    txt = f.read()
    f.close()
    if txt.find('nginx.exe') > -1:
        bUseNginx = True
        nGateWayPort = 9500
        print "��������https���������94XXϵ�ж˿�"
        
    for i in range(1, MAX_USE_SLOT_COUNT + 1):
        if not os.path.isfile(g_sOpenTimeConfigFile % i): #������Ǵ���������Ҫ���
            sResult += "======================================================================<br>����%d: " % i + '<br>'
            nPort = nGateWayPort + i  #���ض˿�
            if IsPortEnable(nPort): #˵���˿ڱ�ռ��
                sResult += '<font style="color:rgb(0,162,0)">���ض˿ڣ� %d ����</font>' % nPort + '<br>'
            else:
                sResult += '<font style="color:rgb(255,0,0)">���ض˿ڣ� %d �ѱ�ռ��</font>' % nPort + '<br>'
            
            nPort = 6400 + i  #�߼��˿�
            if IsPortEnable(nPort): #˵���˿ڱ�ռ��
                sResult += '<font style="color:rgb(0,162,0)">�߼��˿ڣ� %d ����</font>' % nPort + '<br>'
            else:
                sResult += '<font style="color:rgb(255,0,0)">�߼��˿ڣ� %d �ѱ�ռ��</font>' % nPort + '<br>'
                
            nPort = 5400 + i  #DB�˿�
            if IsPortEnable(nPort): #˵���˿ڱ�ռ��
                sResult += '<font style="color:rgb(0,162,0)">DB�˿ڣ� %d ����</font>' % nPort + '<br>'
            else:
                sResult += '<font style="color:rgb(255,0,0)">DB�˿ڣ� %d �ѱ�ռ��</font>' % nPort + '<br>'
                
            nPort = 7400 + i  #��־�˿�
            if IsPortEnable(nPort): #˵���˿ڱ�ռ��
                sResult += '<font style="color:rgb(0,162,0)">��־�˿ڣ� %d ����</font>' % nPort + '<br>'
            else:
                sResult += '<font style="color:rgb(255,0,0)">��־�˿ڣ� %d �ѱ�ռ��</font>' % nPort + '<br>'

    
    return sResult
    
#��ȡ����Ϸ���Ĳ������
def GetSlotInfo(bAllInfo):
    sResult = ''
    f = os.popen("wmic process get ExecutablePath")
    AllAppExecutablePath = f.read()
    f.close() 
    #ɨ�赱ǰ��������������Ϸ��������������Щ���ݿ�
    for i in range(1, MAX_USE_SLOT_COUNT + 1):  
        sTemp = 'λ��%d��'% i
        if os.path.exists(g_sSlotDir % i):  #����Ŀ¼������ֱ������
            sOpenTime = '������'
            if os.path.isfile(g_sServerMerged % i): 
                sOpenTime = '<font style="color:rgb(255,128,0)">�ѱ��Ϸ�</font>'
            elif os.path.isfile(g_sOpenTimeConfigFile % i): #��������п���ʱ���ļ�����˵�����ѿ��� 
                sOpenTime = '<font style="color:rgb(0,162,0)">�ѿ���</font>'
  
            #sLastStartTime = ' '
            sRunning = '<font style="color:rgb(255,0,0)">δ����</font>'
            if ((g_sGameWorldExeFile % i) in AllAppExecutablePath): #������������б�־�����ҽ��̴���
                if os.path.isfile(g_sServerHaveOpend % i):
                    sRunning = '<font style="color:rgb(0,162,0)">������OK</font>'
                else:
                    sRunning = '<font style="color:rgb(255,128,0)">���������е������쳣</font>'
                #sLastStartTime += os.path.getmtime(g_sServerHaveOpend % i).strftime('%Y-%m-%d %H:%M:%S')
            
            nServerIndex = 0
            sSQLHost = 'δ֪'
            sDBName = 'δ֪'
            SPID = 'δ֪'
            nPort = 9400 + i    #���۶�Ӧ�Ķ���˿�
            
            #��ȡ������id  (�����������ȡ���ݿ���Ϣ����Ϊ��ȫ�����ݿ������棬���ֶ�ȡ�ķ�ʽ���������ģ�)
            sFileName = g_sGameWorldConfigFile % i
            if os.path.isfile(sFileName):
                f = file(sFileName) #�������ģʽ��Ĭ���� 'r' ����ģʽ
                while True:
                    line = f.readline() # ����ÿһ��
                    if len(line) == 0: #�����ǻ��п��ж�����ֵ�ģ�Ϊ0�����ʾ�ļ���β
                        break
                        
                    line = line.strip()
                    if 'ServerIndex' in line:
                        tmp = getConfigValue(line)
                        try:
                            nServerIndex = int(tmp)
                        except BaseException, e:
                            printLog( '����%d �ķ�����id�����쳣��'  % i) 
                            print 'except:', e
                    elif 'SPID' in line:
                        SPID = getConfigValue(line)
                     
                f.close()
            #��ȡ���ݿ���Ϣ    
            sFileName = g_sDBServerConfigFile % i
            if os.path.isfile(sFileName):    
                f = file(sFileName) #�������ģʽ��Ĭ���� 'r' ����ģʽ
                while True:
                    line = f.readline() # ����ÿһ��
                    if len(line) == 0: #�����ǻ��п��ж�����ֵ�ģ�Ϊ0�����ʾ�ļ���β
                        break
                        
                    line = line.strip()
                    if 'Host' in line:
                        sSQLHost = getConfigValue(line)
                    elif 'DBName' in line:
                        sDBName = getConfigValue(line)
                        
                f.close()
            
            if bAllInfo: #�Ƚ���ϸ����Ϣ
                sTemp += sOpenTime + '|' + sRunning + '|' + str(nServerIndex) + '��|' + sSQLHost + '|' + sDBName + '|' + SPID + '|' + str(nPort) + '|' + '<br>'
            else: #����Ϣ
                sTemp += sOpenTime + '|' + sRunning + '|' + str(nServerIndex) + '��|' + SPID + '|' + '<br>'
                
        else:
            sTemp += '����Ŀ¼������'
        
        sResult += sTemp
        
    return sResult                
    
#����ָ�����۵����ݿ�������Ϣȥ��ȡ�����ݿ����Ƿ�������ָ��
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
        if cmd == 'start_server': #��ʱֻ�������ָ������
            if (serverid == nServerIndex):
                cur.execute( "delete from `servercmd` where id = %d" % id )
                con.commit()
                
                printLog("��⵽����������ָ��������� serverid = %d" % nServerIndex )
                #��������
                os.system( 'start ' + sSlotStartScript)
            else:
                printLog("����������ָ���쳣�� ������id��һ�£������������� nServerIndex = %d, ��̨ȴ�� serverid = %d , " % (nServerIndex, serverid) )
                 
    cur.close()
    con.close() 

    
def start_script(script_path):
    print script_path
    os.system('start %s' % script_path)
    TXT = 'OK!'
    return TXT
 
#==============================================================================
# ����1�� �������ķ������ĸ��ֲ���������̴߳�����  ������svn���£��ȸ���ָ��ȵȣ�
#==============================================================================
def tcplink(sock, addr):
    try:
        data = sock.recv(4096)
        #print('�յ���������:%s' % data)
        boNeedRestart = False
        sData = "error" #Ĭ���Ǵ��������
        pos = data.find('HTTP/')
        if pos != -1:
            cmd = data[5: pos - 1] #��ȡ��������ļ���
            if 'svn_update' == cmd:
                sData = UpdateSvnPath()
                boNeedRestart = True
            elif 'ping' == cmd:  #���ذ汾��Ϣ������״̬
                sData = 'Running OK!  VERSION = ' + VERSION
            elif 'get_slot_info' == cmd: #��ȡ����Ϸ���Ĳ������(��ϸ��Ϣ������ά�õ�)
                sData = GetSlotInfo(True)
            elif 'get_server_running' == cmd: #��ȡ����Ϸ���Ĳ������(����Ϣ������Ӫ�õ�)
                sData = GetSlotInfo(False)
            elif 'get_slot_version' == cmd: #��ȡ���۵İ汾�ţ�������ڲ鿴ÿ�ΰ汾���������
                sData = GetSlotVersion()
            elif 'get_slot_port_info' == cmd: #��ȡ���۵Ķ˿�ռ����Ϣ�����ڲ�ѯĳ���������Ķ˿��Ƿ��Ѿ�����Ľ���ռ�ã���
                sData = GetSlotPortInfo()
            elif 'slot_update_patch' == cmd: #���۸��²�����ͨ���Ǹ÷������ϵ���������ͬʱ���£�����Ļ��Ӳ�ͬspid��ֻ���ֶ�ȥѡ���Ը��£���
                sData = SlotUpdatePatch()
            elif 'slot_rsf' == cmd: #�ȸ�������    
                sData = SlotRsf()
            elif 'stop_slots' == cmd:# ����ǰ�ر��������е�����
                sData = start_script(r'D:\tools\command\���۵�ֹͣ�Ϳ���\stop_slot.py')
            elif 'start_slots' == cmd:# ���º���������ǰ�رյ�����
                sData = start_script(r'D:\tools\command\���۵�ֹͣ�Ϳ���\start_slot.py')
            elif 'start_process_moniter' == cmd:
                sData = start_script(r'D:\tools\command\�������̼��\�������̼��.py')
            elif 'record_runing_slots' == cmd:
                sData = start_script(r'D:\tools\command\���۵�ֹͣ�Ϳ���\��¼��ǰ���е�����.py')
            elif 'start_log_gate_db' == cmd:
                sData = start_script(r'D:\tools\command\����log_db_gateway��������\start_log_gate_db.py')
                
        #�ظ��ͻ���
        sock.sendall(g_ResponseHeaders % ( len(sData), sData))
        sock.close()
        
        #��Ҫ��������ű�
        if boNeedRestart:
            printLog("������������ű�")
            time.sleep(1)
            os.system("restart.bat")
            os._exit(0)
            
    except BaseException, e: #�����е��쳣������
        sock.close()
        print '�ͻ����쳣:', e

        
#==============================================================================
# ����2�� ������Ӫ������ָ��ļ�������̺߳���  
#==============================================================================     
def checkStartServerAppThreadProc():
    sSlotStartScript = r'D:\GameServer\slot_%d\open_new_server.py'
    while True:
        #ɨ�赱ǰ��������������Ϸ��������������Щ���ݿ�
        for i in range(1, MAX_USE_SLOT_COUNT + 1):  
            if not os.path.exists(g_sSlotDir % i):  #����Ŀ¼������ֱ������
                continue
            if os.path.isfile(g_sServerHaveOpend % i): #������������б�־����˵�����ѿ��������ý��к����ļ��
                continue
            if os.path.isfile(g_sOpenTimeConfigFile % i): #��������п���ʱ���ļ�����˵�����ѿ��������ý��к����ļ��
                continue
            
            nServerIndex = 0
            sSQLHost = ''
            sDBName = ''
            
            #��ȡ������id  (�����������ȡ���ݿ���Ϣ����Ϊ��ȫ�����ݿ������棬���ֶ�ȡ�ķ�ʽ���������ģ�)
            sFileName = g_sGameWorldConfigFile % i
            if os.path.isfile(sFileName):
                f = file(sFileName) #�������ģʽ��Ĭ���� 'r' ����ģʽ
                while True:
                    line = f.readline() # ����ÿһ��
                    if len(line) == 0: #�����ǻ��п��ж�����ֵ�ģ�Ϊ0�����ʾ�ļ���β
                        break
                        
                    line = line.strip()
                    if 'ServerIndex' in line:
                        str = getConfigValue(line)
                        try:
                            nServerIndex = int(str)
                        except BaseException, e:
                            printLog( '����%d �ķ�����id�����쳣��'  % i) 
                            print 'except:', e
                        
                f.close()
            #��ȡ���ݿ���Ϣ    
            sFileName = g_sDBServerConfigFile % i
            if os.path.isfile(sFileName):    
                f = file(sFileName) #�������ģʽ��Ĭ���� 'r' ����ģʽ
                while True:
                    line = f.readline() # ����ÿһ��
                    if len(line) == 0: #�����ǻ��п��ж�����ֵ�ģ�Ϊ0�����ʾ�ļ���β
                        break
                        
                    line = line.strip()
                    if 'Host' in line:
                        sSQLHost = getConfigValue(line)
                    elif 'DBName' in line:
                        sDBName = getConfigValue(line)
                        
                f.close()
                
            #�����������������ָ�����۵����ݿ���Ϣ����ô���Կ�ʼ����ɨ�����ݿ�
            if (nServerIndex > 0) and (nServerIndex < 5000) and (len(sSQLHost) > 0) and (len(sDBName) > 0):
                #��ʼ���Զ�ȡ��ָ̨��
                try:
                    #printLog( '���ڼ��� ����%d �ķ��������ݿ�����ָ�'  % i) 
                    checkStartServerApp(sSlotStartScript%i, nServerIndex, sSQLHost, sDBName)
                except BaseException, e:
                    printLog( '����%d �ķ��������ݿ��������쳣��'  % i) 
                    print 'except:', e
            else:
                if (nServerIndex < 5000):
                    printLog( '��������%d�����ݿ���Ϣ�쳣' % i )
                    print nServerIndex
                    print sSQLHost
                    print sDBName
                
        time.sleep(30)  #ÿ�����ִ��һ�μ���Ƿ��п���ָ��    
        #����
        #printLog( '���ڼ����ȴ���Ӫ���������¼�...' )
              
def main():
    
    #����Ƿ���Ҫ�����������߳�
    threading.Thread(target=checkStartServerAppThreadProc, args=()).start()
    
    print "�����˿ڣ�%d" % SERVER_BIND_PORT
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('0.0.0.0', SERVER_BIND_PORT))
    s.listen(5)

    while True:
        sock, addr = s.accept() # ����һ��������:
        t = threading.Thread(target=tcplink, args=(sock, addr)) # �������߳�������TCP����:
        t.start()
        
try:
    main()   
except BaseException, e: #�����е��쳣������
    print '�������쳣:', e


#raw_input('\n\n\n����ִ����ϣ���������˳�...') 

