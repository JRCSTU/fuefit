' Make Excel fly with Python!
'
' Homepage and documentation: http://xlwings.org
' See also: http://zoomeranalytics.com
'
' Copyright (C) 2014, Zoomer Analytics LLC.
' Version: 0.2.2
'
' License: BSD 3-clause (see LICENSE.txt for details)

Option Explicit
Private Declare PtrSafe Function system Lib "libc.dylib" (ByVal Command As String) As Long

Function Settings(ByRef PYTHON_WIN As String, ByRef PYTHON_MAC As String, _
        ByRef PYTHON_FROZEN As String, ByRef PYTHONPATH As String, ByRef LOG_FILE As String, _
        ByRef PYTHON_FILE As String)
    ' PYTHON_WIN: Directory of Python Interpreter on Windows, "" resolves to default on PATH
    ' PYTHON_MAC: Directory of Python Interpreter on Mac OSX, "" resolves to default on $PATH but NOT .bash_profile!
    ' PYTHON_FROZEN [Optional]: Currently only on Windows, indicate directory of exe file
    ' PYTHONPATH [Optional]: If the source file of your code is not found, add the path here. Otherwise set to "".
    ' LOG_FILE: Directory including file name, necessary for error handling.
    '
    ' For cross-platform compatibility, use backslashes in relative directories
    ' For details, see http://xlwings.org

    PYTHON_WIN = ""
    PYTHON_MAC = GetMacDir("Home") & "/anaconda/bin"
    PYTHON_FROZEN = ThisWorkbook.Path & "\build\exe.win32-2.7"
    PYTHONPATH = ThisWorkbook.Path
    LOG_FILE = ThisWorkbook.Path & "\xlwings_log.txt"
    PYTHON_FILE = ThisWorkbook.Path & "\xlwings_code.py"

End Function
' DO NOT EDIT BELOW THIS LINE

Public Function pandalon_RunPython(PythonCommand As String)
    ' Public API: Runs the Python command, e.g.: to run the function foo() in module bar, call the function like this:
    ' RunPython ("import bar; bar.foo()")

    Dim PYTHON_WIN As String, PYTHON_MAC As String, PYTHON_FROZEN As String, PYTHONPATH As String, PYTHON_FILE As String
    Dim LOG_FILE As String, DriveCommand As String, PythonTxt As String
    Dim ExitCode As Integer, Res As Integer

    ' Get the settings by using the ByRef trick
    Res = Settings(PYTHON_WIN, PYTHON_MAC, PYTHON_FROZEN, PYTHONPATH, LOG_FILE, PYTHON_FILE)

    ' Call Python platform-dependent
    #If Mac Then
        Application.StatusBar = "Running..."  ' Non-blocking way of giving feedback that something is happening
        ExcecuteMac PythonCommand, PYTHON_MAC, PYTHON_FILE, LOG_FILE, PYTHONPATH
    #Else
        ExecuteWindows False, PythonCommand, PYTHON_WIN, PYTHON_FILE, LOG_FILE, PYTHONPATH
    #End If
End Function

Sub ExcecuteMac(Command As String, PYTHON_MAC As String, PYTHON_FILE As String, LOG_FILE As String, Optional PYTHONPATH As String)
    ' Run Python with the "-c" command line switch: add the path of the python file and run the
    ' Command as first argument, then provide the WORKBOOK_FULLNAME and "from_xl" as 2nd and 3rd arguments.
    ' Finally, redirect stderr to the LOG_FILE and run as background process.

    Dim PythonInterpreter As String, PythonTxt As String, WORKBOOK_FULLNAME As String, Log As String, PythonExec As String
    Dim Res As Integer

    ' Delete Log file just to make sure we don't show an old error
    On Error Resume Next
        KillFileOnMac ToMacPath(ToPosixPath(LOG_FILE))
        KillFileOnMac ToMacPath(ToPosixPath(PYTHON_FILE))
    On Error GoTo 0

    ' Transform from MacOS Classic path style (":") and Windows style ("\") to Bash friendly style ("/")
    PYTHONPATH = ToPosixPath(PYTHONPATH)
    LOG_FILE = ToPosixPath(LOG_FILE)
    PythonInterpreter = ToPosixPath(PYTHON_MAC & "/python")
    WORKBOOK_FULLNAME = ToPosixPath(ThisWorkbook.FullName)

    ' Build the command (ignore warnings to be in line with Windows where we only show the popup if the ExitCode <>0
    PythonTxt = PythonInterpreter & " -W ignore -c ""import sys; sys.path.append(r'" & PYTHONPATH & "'); " & Command & """ "


    ' Send the command to the shell. Courtesy of Robert Knight (http://stackoverflow.com/a/12320294/918626)
    ' Since Excel blocks AppleScript as long as a VBA macro is running, we have to excecute the call as background call
    ' so it can do its magic after this Function has terminated. Python calls ClearUp via the atexit handler.
    PythonExec = PythonTxt & """" & WORKBOOK_FULLNAME & """ ""from_xl"" >" & Chr(34) & LOG_FILE & Chr(34) & " 2>&1 &"
    Debug.Print ("PYTHON_EXEC: " & PythonExec & vbCrLf & "PYTHON_CODE: " & PythonTxt)
    Res = system(PythonExec)

    ' If there's a log at this point (normally that will be from the Shell only, not Python) show it and reset the StatusBar
    Log = ReadFile(LOG_FILE)
    If Log = "" Then
        Exit Sub
    Else
        ShowError (LOG_FILE)
        Application.StatusBar = False
    End If

End Sub

Sub ExecuteWindows(IsFrozen As Boolean, Command As String, PYTHON_WIN As String, _
        PYTHON_FILE As String, LOG_FILE As String, Optional PYTHONPATH As String)
    ' Call a command window and change to the directory of the Python installation or frozen executable
    ' Note: If Python is called from a different directory with the fully qualified path, pywintypesXX.dll won't be found.
    ' This seems to be a general issue with pywin32, see http://stackoverflow.com/q/7238403/918626

    Dim Wsh As Object
    Dim WaitOnReturn As Boolean: WaitOnReturn = True
    Dim WindowStyle As Integer: WindowStyle = 0
    Set Wsh = CreateObject("WScript.Shell")
    Dim DriveCommand As String, PythonTxt As String, PythonExec As String
    Dim ExitCode As Integer

    If Left$(PYTHON_WIN, 2) Like "[A-Z]:" Then
        ' If Python is installed on a mapped or local drive, change to drive, then cd to path
        DriveCommand = Left$(PYTHON_WIN, 2) & " & cd " & PYTHON_WIN & " & "
    ElseIf Left$(PYTHON_WIN, 2) = "\\" Then
        ' If Python is installed on a UNC path, temporarily mount and activate a drive letter with pushd
        DriveCommand = "pushd " & PYTHON_WIN & " & "
    End If

    PythonTxt = "import sys; sys.path.append(r'" & PYTHONPATH & "'); " & Command
    Call WriteFile(PYTHON_FILE, PythonTxt)

    ' Create a Python script thats adds the Workb-path into the `sys.path` and then run it
    ' with the workbook-fullname and "from_xl" as 1st and 2nd arguments.
    ' Then redirect stderr to the LOG_FILE and wait for the call to return.
    PythonExec = "cmd.exe /C " & DriveCommand & _
                   "python """ & PYTHON_FILE & """ " & _
                   """" & ThisWorkbook.FullName & """ ""from_xl"" 2> """ & LOG_FILE & """ "
    Debug.Print ("PYTHON_EXEC: " & PythonExec & vbCrLf & "PYTHON_CODE: " & PythonTxt)
    ExitCode = Wsh.Run(PythonExec, WindowStyle, WaitOnReturn)

    'If ExitCode <> 0 then there's something wrong
    If ExitCode <> 0 Then
        Call ShowError(LOG_FILE)
    End If

    ' Delete file after the error message has been shown
    On Error Resume Next
        Kill LOG_FILE
        Kill PYTHON_FILE
    On Error GoTo 0

    ' Clean up
    Set Wsh = Nothing
End Sub

Public Function RunFrozenPython(Executable As String)
    ' Runs a Python executable that has been frozen by cx_Freeze or py2exe. Call the function like this:
    ' RunFrozenPython("frozen_executable.exe"). Currently not implemented for Mac.

    Dim PYTHON_WIN As String, PYTHON_MAC As String, PYTHON_FROZEN As String, PYTHONPATH As String, LOG_FILE As String, PYTHON_FILE As String
    Dim Res As Integer

    ' Get the settings by using the ByRef trick
    Res = Settings(PYTHON_WIN, PYTHON_MAC, PYTHON_FROZEN, PYTHONPATH, LOG_FILE, PYTHON_FILE)

    ' Call Python
    #If Mac Then
        MsgBox "This functionality is not yet supported on Mac." & vbNewLine & _
               "Please run your scripts directly in Python!", vbCritical + vbOKOnly, "Unsupported Feature"
    #Else
        ExecuteWindows True, Executable, PYTHON_FROZEN, PYTHON_FILE, LOG_FILE
    #End If
End Function

Function ReadFile(ByVal FileName As String)
    ' Read a text file

    Dim Content As String
    Dim Token As String
    Dim FileNum As Integer

    #If Mac Then
        FileName = ToMacPath(FileName)
    #End If

    FileNum = FreeFile
    Content = ""

    ' Read Text File
    'On Error GoTo exit_sub
    Open FileName For Input As #FileNum
        Do While Not EOF(FileNum)
            Line Input #FileNum, Token
            Content = Content & Token & vbCr
        Loop
    Close #FileNum

exit_sub:
    ReadFile = Content
End Function

Sub WriteFile(ByVal FileName As String, ByVal Txt As String)
    Dim FileNum As Integer
    
    #If Mac Then
        FileName = ToMacPath(FileName)
    #End If
    
    FileNum = FreeFile
    Open FileName For Output As #FileNum
        Print #FileNum, Txt
    Close #FileNum
End Sub

Sub ShowError(FileName As String)
    ' Shows a MsgBox with the content of a text file

    Dim Content As String

    Content = ReadFile(FileName)
    #If Win32 Or Win64 Then
        Content = Content & vbCr
        Content = Content & "Press Ctrl+C to copy this message to the clipboard."
    #End If
    MsgBox Content, vbCritical, "Error"
End Sub

Function ToPosixPath(ByVal MacPath As String) As String
    'This function accepts relative paths with backward and forward slashes: ThisWorkbook & "\test"
    ' E.g. "MacintoshHD:Users:<User>" --> "/Users/<User>"

    Dim s As String

    MacPath = Replace(MacPath, "\", ":")
    MacPath = Replace(MacPath, "/", ":")
    s = "tell application " & Chr(34) & "Finder" & Chr(34) & Chr(13)
    s = s & "POSIX path of " & Chr(34) & MacPath & Chr(34) & Chr(13)
    s = s & "end tell" & Chr(13)
    ToPosixPath = MacScript(s)
End Function

Function GetMacDir(Name As String) As String
    ' Get Mac special folders. Protetcted so they don't exectue on Windows.

    Dim Path As String

    #If Mac Then
        Select Case Name
            Case "Home"
                Path = MacScript("return (path to home folder) as string")
             Case "Desktop"
                Path = MacScript("return (path to desktop folder) as string")
            Case "Applications"
                Path = MacScript("return (path to applications folder) as string")
            Case "Documents"
                Path = MacScript("return (path to documents folder) as string")
        End Select
            GetMacDir = Left$(Path, Len(Path) - 1) ' get rid of trailing ":"
    #Else
        GetMacDir = ""
    #End If
End Function

Function ToMacPath(PosixPath As String) As String
    ' This function transforms a Posix Path into a MacOS Path
    ' E.g. "/Users/<User>" --> "MacintoshHD:Users:<User>"

    ToMacPath = MacScript("set mac_path to POSIX file " & Chr(34) & PosixPath & Chr(34) & " as string")
End Function

Function KillFileOnMac(Filestr As String)
    'Ron de Bruin
    '30-July-2012
    'Delete files from a Mac.
    'Uses AppleScript to avoid the problem with long file names

    Dim ScriptToKillFile As String

    ScriptToKillFile = "tell application " & Chr(34) & "Finder" & Chr(34) & Chr(13)
    ScriptToKillFile = ScriptToKillFile & "do shell script ""rm "" & quoted form of posix path of " & Chr(34) & Filestr & Chr(34) & Chr(13)
    ScriptToKillFile = ScriptToKillFile & "end tell"

    On Error Resume Next
        MacScript (ScriptToKillFile)
    On Error GoTo 0
End Function

Private Sub CleanUp()
    'On Mac only, this function is being called after Python is done (using Python's atexit handler)

    Dim PYTHON_WIN As String, PYTHON_MAC As String, PYTHON_FROZEN As String, PYTHONPATH As String
    Dim PYTHON_FILE As String, LOG_FILE As String
    Dim Res As Integer

    'Get LOG_FILE
    Res = Settings(PYTHON_WIN, PYTHON_MAC, PYTHON_FROZEN, PYTHONPATH, LOG_FILE, PYTHON_FILE)
    LOG_FILE = ToPosixPath(LOG_FILE)

    'Show the LOG_FILE as MsgBox if not empty
    If ReadFile(LOG_FILE) <> "" Then
        Call ShowError(LOG_FILE)
    End If

    'Clean up
    Application.StatusBar = False
    Application.ScreenUpdating = True
End Sub

