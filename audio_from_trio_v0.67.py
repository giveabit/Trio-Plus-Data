# -*- coding: utf-8 -*-
#!/usr/bin/env python3


# ++++++++++++++++++++++++++++++++++++++++++++
# IMPORTS
# ++++++++++++++++++++++++++++++++++++++++++++
import sys, time, os
from glob import glob

# ++++++++++++++++++++++++++++++++++++++++++++
# GLOBALS
# ++++++++++++++++++++++++++++++++++++++++++++
offsetAudio = 138032 #bytes changed from 170800
chunkSize = 32768 #bytes
wavDir = 'Trio_wav_export'
headerFile = wavDir+'/header.bin'
trioFileExtension = '.tlsd'

# # ++++++++++++++++++++++++++++++++++++++++++++
# # DEBUG?
# # ++++++++++++++++++++++++++++++++++++++++++++
debug = False
debugDir = 'debug'

# ++++++++++++++++++++++++++++++++++++++++++++
# FUNCTIONS
# ++++++++++++++++++++++++++++++++++++++++++++
def intro():
    print('-----------------------------------------------------------------------------')
    print('|                                                                    @@     |')
    print('|                                                                    @@     |')
    print('|                                                                 @@@@@@@@  |')
    print('|                                                                    @@     |')
    print('| @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@     @@@      @@@@@@@@@@@@@       @@     |')
    print('|        @@@         @@@         @@@    @@@    @@@@          @@@            |')
    print('|        @@@         @@@          @@@   @@@   @@@             @@@@          |')
    print('|        @@@         @@@          @@@   @@@  @@@@              @@@          |')
    print('|        @@@         @@@        @@@@    @@@  @@@               @@@@         |')
    print('|        @@@         @@@@@@@@@@@@@      @@@  @@@                @@@         |')
    print('|        @@@         @@@    @@@@        @@@  @@@               @@@          |')
    print('|        @@@         @@@      @@@       @@@   @@@              @@@          |')
    print('|        @@@         @@@       @@@      @@@   @@@@            @@@           |')
    print('|        @@@         @@@        @@@@    @@@     @@@@       @@@@@            |')
    print('|        @@@         @@@          @@@   @@@        @@@@@@@@@@               |')
    print('-----------------------------------------------------------------------------')
    print('export tool - giveabit@mail.ru')
    time.sleep(0.5)

def init():
    if not os.path.isdir(wavDir):
        os.mkdir(wavDir)
    fileList = glob('*'+trioFileExtension)

    if debug:
        if not os.path.isdir(debugDir):
            os.mkdir(debugDir)
    return fileList

def readBytes(fileName, offset):
    with open(fileName, 'rb') as f:
        f.seek(offset)
        buffer = f.read()
    return buffer

def getPartInfo(data, debugFile):
    parts = []
    offsetsTemp = []
    offsetsVerifiedStarts = []
    offsetsVerifiedEnds = []
    previous = offsetAudio
    for i in range(1300, 1319, 4):
        if not data[i:i+4] == b'\x00' * 4:
            parts.append(data[i:i+4])
    if len(parts) == 0:
        sys.stdout.write('\t\t\t[-] no parts trained.\r')
        return 0
    # DEBUG
    if debug:
        with open(debugFile,'w') as f:
            f.write('\nAUDIO PARTS FROM HEADER:\n')
    # END

    # raw part information according to header 1300...1319
    for item in parts:
        start, overdub = findAudioStart(data, previous)
        offsetsTemp.append(start)
        offsetsTemp.append(int.from_bytes(item, byteorder='little')+previous)
        if overdub:
            offsetsTemp.append(start+chunkSize)
            offsetsTemp.append(int.from_bytes(item, byteorder='little') + previous)
        previous = offsetsTemp[-1]
    # DEBUG
    if debug:
        temp = offsetsTemp
        it = iter(temp)
        temp = zip(it,it)
        with open(debugFile, 'a') as f:
            f.write('\ninitial values:\n')
            for item in temp:
                f.write(str(item)+'\n')
        temp=[]
    # END
    it = iter(offsetsTemp)
    offsetsTemp = zip(it, it)

    # verify the start position
    for item in offsetsTemp:
        start, end = item
        buffer = data[start:start+chunkSize]
        if not verifyZeroBlock(buffer):
            offsetsVerifiedStarts.append(start)
            offsetsVerifiedStarts.append(end)
    if len(offsetsVerifiedStarts) == 0:
        sys.stdout.write('\t\t\t[-] no parts recorded.\r')
        return 0
    it = iter(offsetsVerifiedStarts)
    offsetsVerifiedStarts = zip(it, it)

    # verify endings
    for item in offsetsVerifiedStarts:
        start, end = item
        buffer = data[end-16:end]
        while buffer == b'\x00' * 16:
            end -= 16
            buffer = data[end-16:end]
        offsetsVerifiedEnds.append(start)
        offsetsVerifiedEnds.append(end)
    # DEBUG
    if debug:
        temp = offsetsVerifiedEnds
        it = iter(temp)
        temp = zip(it,it)
        with open(debugFile, 'a') as f:
            f.write('\nfinal values for further processing:\n')
            for item in temp:
                f.write(str(item)+'\n')
    # END
    it = iter(offsetsVerifiedEnds)
    offsetsVerifiedEnds = zip(it, it)

    return  offsetsVerifiedEnds

def findAudioStart(data, offset):
    overdub = 0
    buffer = data[offset:offset+chunkSize]
    if verifyZeroBlock(buffer):
        return offset+chunkSize, overdub
    else:
        overdub = 1
        return offset, overdub

def verifyZeroBlock(buffer):
    if buffer == b'\x00'*chunkSize:
        return True
    else:
        return False

def formAudioParts(boundaries, data, debugFile):
    # DEBUG
    if debug:
        with open(debugFile,'a') as f:
            f.write('\nAUDIO PARTS:\n')
    # END
    audioParts = []
    for item in boundaries:
        temp = []
        start, end = item
        index = start
        while index + chunkSize < end:
            temp.append(data[index:index+chunkSize])
            # DEBUG
            if debug:
                with open(debugFile,'a') as f:
                    f.write(str(index)+'-'+str(index+chunkSize)+'\n')
            # END
            index += 2*chunkSize
        index += chunkSize
        temp.append(data[index:end])
        # DEBUG
        if debug:
            with open(debugFile,'a') as f:
                f.write(str(index)+'-'+str(end-1)+'\n')
                f.write('-'*30+'\n')
        # END
        audioParts.append(temp)
    return audioParts

def outFile(fileName, writeBytes):
    with open(fileName,'ab') as f:
        f.write(writeBytes)
    return

def writeHeader(sizeAudio):
    data = []
    data.append('RIFF'.encode())
    fileSize = sizeAudio+44-8 #file-fileSize (equals file-fileSize - 8); wav header = 44 bytes
    sampleRate = 44100
    numberChannels = 1
    bitsPerSample = 16
    byteRate = int(sampleRate*bitsPerSample*numberChannels/8)
    blockAlign = int(numberChannels*bitsPerSample/8)
    subChunk2Size = fileSize-44

    data.append(fileSize.to_bytes(4,'little'))
    data.append('WAVEfmt '.encode())
    data.append((16).to_bytes(4,'little')) #Subchunk1Size    16 for PCM
    data.append((1).to_bytes(2,'little')) #Type of format (1 is PCM)
    data.append(numberChannels.to_bytes(2,'little')) #Number of Channels
    data.append(sampleRate.to_bytes(4,'little')) #sample rate
    data.append(byteRate.to_bytes(4,'little'))# byteRate = sample Rate * BitsPerSample * Channels/ 8
    data.append(blockAlign.to_bytes(2,'little'))#BlockAlign= NumChannels * BitsPerSample/8
    data.append(bitsPerSample.to_bytes(2,'little')) # BitsPerSample
    data.append('data'.encode())
    data.append(subChunk2Size.to_bytes(4,'little'))#data-block fileSize (equals file-fileSize - 44)

    with open(headerFile, 'wb') as f:
        for item in data:
            f.write(item)

def exportTrioHeader(data, fileName):
    fileName = debugDir+'/'+fileName+'.header.bin'
    header = []
    header = data[:offsetAudio]
    outFile(fileName, header)

# ++++++++++++++++++++++++++++++++++++++++++++
#              M    A    I    N
# ++++++++++++++++++++++++++++++++++++++++++++
intro()
fileList = init()
filesTotal = str(len(fileList))
nowTotal = time.time()
for fileName in fileList:
    print('\nprocessing: '+fileName)
    now = time.time()
    data = readBytes(fileName, 0)

    if debug:
        exportTrioHeader(data, fileName)
        debugFile = debugDir+'/'+fileName+'.DBG.txt'
    else:
        debugFile = None

    sys.stdout.write('\t\t\t[x] locating parts.\r')
    parts = getPartInfo(data, debugFile)
    if parts:
        sys.stdout.write('\n\t\t\t[x] gathering audio parts.')
        audioBlocks = formAudioParts(parts, data, debugFile)

        sys.stdout.write('\n\t\t\t[x] writing files.')
        foo = 0
        for part in audioBlocks:
            if len(audioBlocks) > 1:
                outFileName = wavDir+'/'+fileName.split('.')[0]+'_'+str(foo)+'.tmp'
            else:
                outFileName = wavDir+'/'+fileName.split('.')[0]+'.tmp'
            for audioData in part:
                outFile(outFileName, audioData) #first write all the plain audio data
            if not len(part):
                print('\nWARNING: no Data for: '+outFileName)

            try:
                sizeAudio = os.path.getsize(outFileName) #we need the size to write a correct wav header
                writeHeader(sizeAudio) # do it!
                with open(headerFile, "ab") as f1, open(outFileName, "rb") as f2:
                    f1.write(f2.read()) #now pump the data at the end of the header
                wavFile = outFileName[:-3]+'wav'
                if os.path.isfile(wavFile):
                    os.remove(wavFile)
                os.rename(headerFile, wavFile) # rename nicely!
                os.remove(outFileName) # and clean up ;-)
            except:
                print('\nWe encountered an error while processing: '+outFileName)
                e = sys.exc_info()[0]
                print('The error message reads: ', e,'\n')
                if os.path.isfile(outFileName):
                        os.remove(outFileName)
            foo += 1


    runningTime = str(round(time.time()-now,1))+' seconds.\n'
    sys.stdout.write('\n\t\t\t[x] finished in: '+runningTime)
runningTimeTotal = str(round(time.time()-nowTotal, 1))+' seconds.\n'
sys.stdout.write('\n'+filesTotal+' files overall processed in: '+runningTimeTotal)
input('<ENTER>')