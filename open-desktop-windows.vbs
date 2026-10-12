Option Explicit
Dim shell, fs, folder, python, launcher
Set shell = CreateObject("WScript.Shell")
Set fs = CreateObject("Scripting.FileSystemObject")
folder = fs.GetParentFolderName(WScript.ScriptFullName)
python = fs.BuildPath(folder, ".desktop-venv\Scripts\pythonw.exe")
launcher = fs.BuildPath(folder, "desktop_app.py")
If Not fs.FileExists(python) Then
  MsgBox "Chay install-desktop-windows.bat mot lan de cai ung dung.", 48, "Freelance Desk"
  WScript.Quit 1
End If
shell.CurrentDirectory = folder
shell.Run Chr(34) & python & Chr(34) & " " & Chr(34) & launcher & Chr(34), 0, False
