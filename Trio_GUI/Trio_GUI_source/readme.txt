Hi dear user,
all source files are located in the <python3-files> folder.

With the current source, I was able to build a fully working windows binary using
<http://www.pyinstaller.org/downloads.html>

You may be better at these tasks but here's how I did it:

01 compile a first round with this command:
pyinstaller --onefile --noconsole Trio_GUI.py

-> this will give you a <Trio_GUI.spec> file specific for your system

02 open and modify the <Trio_GUI.spec> file as indicated below:

...
exe = EXE(pyz,
          a.scripts,
          a.binaries,
		  directly here, insert the following line: ->
		  Tree('resource_files', prefix='resource_files'),
		  ...
		  
03 compile a second round with this command:
pyinstaller --clean --noconsole --onefile Trio_GUI.spec

04 you should now have a working binary in the <dist> folder

NOTE:
For some unknown reason, under linux/ubuntu the favicon.ico file will not be accepted and
the code will crash. Disabling the favicon in the <Trio_GUI.py> file will get the code working:
FAVICO = None (simply remove the hashtag # in the source code).

If you want to run or compile the source code, you will need to install these dependencies first:
- pyaudio
- pillow

Further, window handling under linux seems a bit different than on windows. If I find the time,
I will tweak the code and compile a linux binary.

Cheers!
giveabit@mail.ru
