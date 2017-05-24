# Trio-Plus-Data
current version: release 0.73 as of 2017-04-04<br>
<i> current development under 'Trio+Tool' branch</i><br>
<i> updating the Trio+ hardware with 'TrioUpdaterInstaller_v2.0.2.exe' from Digitech website might be necessary</i>

CONTENTS:<br>
00 <b>Status-miniblog<br></b>
01 TLDR<br>
02 Project Status<br>
03 Working<br>
04 Not working<br>
05 Getting started<br>
06 Going further<br>

<br>00 miniblog:<br>
<b>2017-05-24</b><br>
Working on the 'upload audio' to a song functionality. Have not worked out how to determine which part of the interleaved audio that has been recorded is the one actually being in use currently. As a last resort, one could ask the user to decide but I am still hoping to figure that out. Maybe I will be pushing some code in the next weeks. Had to attend to other issues the last weeks.<br>
Cheers!<br><br>
2017-04-04<br>
New release (0.73, recommended). Copy, erase, move parts implemented.<br>
Cheers!<br><br>
2017-03-13<br>
New release - bugfixes. I hate bugs ;-). We're still beta with the editing functions!
Cheers!<br>
<br>2017-03-12<br>
New Release - check it out.
Cheers!

<br>01 TLDR:<br>
* Ultimate goal is to extract audio and midi data from the Digitech Trio Plus pedal's SD card for further use in your preferred DAW.

see: http://digitech.com/en/products/trio-plus

* Written in PYTHON3 (no dependencies)
* Tested on Windows, Linux


<br>02 Project Status:<br>
good to work with; alway get latest release!

<br>03 Working:<br>
extract audio; copy, move and erase parts.<br>

<br>04 Not working:<br>
upload audio to part;<br>
Any MIDI data support is missing at the moment

<br>05 Getting started:<br>
download and install the latest Python version (3.x) for your computer from
https://www.python.org/downloads/

Record some stuff with the Trio Plus

Export the songs (the single files) onto your computer using the Digitech Trio Manager
http://digitech.com/en/softwares/

Download the latest RELEASE version of the script. Unpack the .zip file. Place the exported songs (*.tlsd) from the SD card into the unpacked folder and start 'The_Trio+_Tool.py'. Follow the instructions.

-> LINUX users remember: you might need to change the endlines of the script (as it was edited on windows) <-

The subfolder 'Trio_wav_export' will be created and the audio contents of the songs will be written herein

<br>06 Going further<br>
NEED YOUR HELP to further reverse-engineering the data.<br>
Look at my 'findings.txt' for what I found out so far

Let's have fun!
