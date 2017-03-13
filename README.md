# Trio-Plus-Data
current version: 0.67 as of 2016-12-06<br>

CONTENTS:<br>
00 <b>Status-miniblog<br></b>
01 TLDR<br>
02 Project Status<br>
03 Working<br>
04 Not working<br>
05 Getting started<br>
06 Going further<br>

<br>00 miniblog:<br>
<b>2017-03-13<br></b>
New Release - bugfixes. I hate bugs ;-). We're still beta with the editing functions!
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
(v 0.50) extract audio from *.tlsd file if no overdub loops have been recorded<br>
(v 0.51) also separating the different part sections of the song (multiple wave files as output)<br>
(v 0.60) also extracting different part sections when these include overdubs; although the overdubbed parts are still buggy<br>
(v 0.61) mostly bugfixes, overall code improvements, enhanced detection for overdubbed recordings<br>
(v 0.62) even more bugfixes<br>
(v 0.63) performance greatly improved to lightning speed (!), nicer text output, ASCII art intro<br>
(v 0.65) complete re-write of key routines. Will be working better with overdub-parts in the future. Little buggy with the audio part endings (which were smooth in older version 0.63) - to be corrected. Is cleaning up leftovers better if something goes wrong. Fixed logical bug with zero block detection (still key issue). Extracts header files in debug mode. Contents of debug files changed.<br>
(v 0.66) bug-fixed sloppy endings.<br>
<b>NEW, recommended - (v 0.67)</b> HUGE LEAP FORWARD - HEADER PARTLY DECRYPTED - information was used to re-write the code. Now correctly deals with single overdubs. Multiple overdubs seem to work in most cases.<br>

<br>04 Not working:<br>
multiple overdub loops are yet to be confirmed working<br>
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
