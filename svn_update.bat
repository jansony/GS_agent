:: ��һ�ַ�ʽ    ȱ���ǳ��ֳ�ͻ������֪��
:: svn update D:\Game\QQDouSheng_Client\assets
:: svn update D:\WWW\QQ_LTZS_Client\assets

:: �ڶ��ַ�ʽ   �ʺ�windowsƽ̨   ע�⣺������·������ *^  ��ƴ��ÿ��Ŀ¼�����һ��Ŀ¼����Ҫ������ţ�
@echo off
set Paths=D:\tools*^
D:\temp

TortoiseProc.exe /command:update /path:"%Paths%" /closeonend:1

@echo svn update OK!