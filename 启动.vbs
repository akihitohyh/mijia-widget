' 启动米家桌面插件（隐藏命令行窗口）
Set WshShell = CreateObject("WScript.Shell")

' 获取当前目录
strPath = Left(WScript.ScriptFullName, InStrRev(WScript.ScriptFullName, "\") - 1)

' 检查 exe 是否存在
Dim fso
Set fso = CreateObject("Scripting.FileSystemObject")

If fso.FileExists(strPath & "\dist\米家桌面插件.exe") Then
    WshShell.Run """" & strPath & "\dist\米家桌面插件.exe"""", 0, False
Else
    WshShell.Run "pythonw """ & strPath & "\main_widget.py"""", 0, False
End If

Set WshShell = Nothing
