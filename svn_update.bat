:: 第一种方式    缺点是出现冲突不容易知道
:: svn update D:\Game\QQDouSheng_Client\assets
:: svn update D:\WWW\QQ_LTZS_Client\assets

:: 第二种方式   适合windows平台   注意：如果多个路径，用 *^  来拼接每个目录，最后一个目录不需要这个符号！
@echo off
set Paths=D:\tools*^
D:\temp

TortoiseProc.exe /command:update /path:"%Paths%" /closeonend:1

@echo svn update OK!