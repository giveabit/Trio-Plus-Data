# Trio-Plus-Data
current version: release 0.72 as of 2017-03-29<br>
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
<b>2017-03-29</b><br>
New release (0.72, recommended). Copy does work except copy to part 4, which is strange. Hummm. Nevertheless - check it out.<br>
Update to the 'Trio+ Addresses.xlsx' file (knowledgebase of all known addresses)<br>
Cheers!<br><br>
2017-03-13<br>
New release - bugfixes. I hate bugs ;-). We're still beta with the editing functions!
Cheers!<br>
<br>2017-03-12<br>
New Release - check it out.
Cheers!<br><br>
2017-03-08<br>
It's been silent a while but behind the scenes work is going on. Currently I got a request to implement some sort of song manipulation: copy, delete, move parts as well as uploading audio to a part. I had to do a major re-write and add a whole lot of code. At the moment, I am working on the 'copy' function. While programming progress is good I still do not know what the Trio+ will come up with when copying parts. I still have not decoded the bass/drum functions of the Trio+ so it might well be that audio copy from one part to another is possible but there might be no bass/drum in the newly copied part. We will see...
Release estimate: 'when ready' (TM) - maybe end of march ?!
Cheers!

<br>01 TLDR:<br>
* Ultimate goal is to extract audio and midi data from the Digitech Trio Plus pedal's SD card for further use in your preferred DAW.

see: http://digitech.com/en/products/trio-plus

* Written in PYTHON3 (no dependencies)
* Tested on Windows, Linux


<br>02 Project Status:<br>
Beta - as of version 0.67

<br>03 Working:<br>
extract audio; copy parts (buggy); erase parts (dirty, needs cleaning)<br>

<br>04 Not working:<br>
copy to part 4; upload audio to part; move part not confirmed to be working correctly<br>
Any MIDI data support is missing at the moment

<br>05 Getting started:<br>
download and install the latest Python version for your computer from
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
