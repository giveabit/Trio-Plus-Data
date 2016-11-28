# Trio-Plus-Data
<b>current version: 0.61 </b>as of 2016-11-28<br>

CONTENTS:<br>
01 TLDR<br>
02 Project Status<br>
03 Working<br>
04 Not working<br>
05 Getting started<br>
06 Going further<br>


<br>01 TLDR:<br>
* Ultimate goal is to extract audio and midi data from the Digitech Trio Plus pedal's SD card for further use in your preferred DAW.

see: http://digitech.com/en/products/trio-plus

* Written in PYTHON3 (no dependencies)
* Tested on Windows, Linux


<br>02 Project Status:<br>
ALPHA

<br>03 Working:<br>
Extract audio from *.tlsd file if no overdub loops have been recorded<br>
(v 0.51) also separating the different part sections of the song (multiple wave files as output)<br>
(v 0.60) also extracting different part sections when these include overdubs; although the overdubbed parts are still buggy<br>
<b>NEW -(v 0.61)</b> mostly bugfixes, overall code improvements, enhanced detection for overdubbed recordings<br>

<br>04 Not working:<br>
overdub loops are exported but are buggy (possibly audio chunk alignment issue)<br>
Any MIDI data support is missing at the moment

<br>05 Getting started:<br>
download and install the latest Python version for your computer from
https://www.python.org/downloads/

Record some stuff with the Trio Plus

Export the songs (the single files) onto your computer using the Digitech Trio Manager
http://digitech.com/en/softwares/

Place the Python script from this page (audio_from_trio_vX.X.py) in the same directory as the exported songs (*.tlsd) from the SD card

Fire up the script! -> LINUX users remember: you might need to change the endlines of the script (as it was edited on windows) <-

The subfolder 'Trio_wav_export' will be created and the audio contents of the songs will be written herein

<br>06 Going further<br>
NEED YOUR HELP to further reverse-engineering the data.<br>
Look at my 'findings.txt' for what I found out so far

Let's have fun!
