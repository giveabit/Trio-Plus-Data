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
##offsetFF = 127288 # always FF FF FF FF
chunkSize = 32768 #bytes
wavDir = 'Trio_wav_export'
headerFile = wavDir+'/header.bin'
trioFileExtension = '.tlsd'

# ++++++++++++++++++++++++++++++++++++++++++++
# DEBUG? QUICKSEARCH OPTION?
# ++++++++++++++++++++++++++++++++++++++++++++
debug = True
debugDir = 'debug'

quick = True # --->>> v0.63 keep as optional until stable <<<---
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
    time.sleep(1)

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

def findAudioStart(data):
    buffer = data[offsetAudio:offsetAudio+chunkSize]
    if verifyZeroBlock(buffer):
        return offsetAudio+chunkSize
    else:
        return offsetAudio

def getZeroBlocks(data, debugFile):
    fileSize = len(data)
    zeroBlocks = []
    position = offsetAudio
    success = True
    while position <= fileSize-chunkSize:
        if position % 1000 == 0:
            reportProgress(position, fileSize)

        buffer = data[position:position+chunkSize]

        if verifyZeroBlock(buffer) and position % 16 == 0:
            # zero blocks always start aligned to n*16 bytes offsets
            # yields false results if omitted!!!
            zeroBlocks.append(position)
            #zeroBlocks.append(position+chunkSize) # remove
            position += chunkSize
            success = True
        else:
            if success == True and quick:# --->>> remove second condition if running stable <<<---
                position, success = quickStep(data, position)
            position += 1
    # DEBUG
    if debug:
        temp1 = zeroBlocks
        temp2 = []
        align = []
        for item in temp1:
            temp2.append(item)
            temp2.append(item+chunkSize-1)
            align.append((item-offsetAudio) % chunkSize)
        it = iter(temp2)
        temp2 = zip(it,it)
        it = iter(align)
        temp2 = zip(temp2,it)
        with open(debugFile, 'w') as f:
            f.write('ZERO BLOCKS LIST:\n')
            for item in temp2:
                f.write(str(item)+'\n')
    # END
    reportProgress(1,1) # =100 %
    return fileSize, zeroBlocks

def verifyZeroBlock(buffer):
    if buffer == b'\x00'*chunkSize:
        return True
    else:
        return False

def quickStep(data, position):
    success = False
    positionOld = position
    position = position + chunkSize-1
    buffer = data[position:position+1]
    if buffer == b'\x00':
        bufferL = data[position-1:position]
        bufferR = data[position+1:position+2]
        if bufferL == b'\x00' and bufferR == b'\x00':
            return positionOld, success
        if not bufferL == b'\x00':
            success = True
            return position-1, success
        if not bufferR == b'\x00':
            success = True
            return position, success
    else:
        success = True
        return position, success

def reportProgress(position, total):
    progress = float(position/total)*100
    sys.stdout.write("progress: %.2f%%   \r" % (progress))
    sys.stdout.flush()

def locateBoundaries(zeroBlocks, start, fileSize, debugFile):
    audioStart = []
    audioEnd = []
    audioStart.append(start)
    modulo = 0
    for blockStart in zeroBlocks:
        if not (blockStart-offsetAudio) % chunkSize == modulo:
            audioEnd.append(blockStart-1) # last vaild audio byte
            modulo = (blockStart-offsetAudio) % chunkSize # needs to be re-set
            # offset in bytes for unaligned (off 32 k steps) start of zero chunk
            # is definitely the END of an audio block
            if not blockStart+chunkSize+1 > fileSize:
                audioStart.append(blockStart+chunkSize) # first vaild audio byte
                # it also means, that there is the start of a new segment at +32 k
    position = fileSize
    while data[position-1:position] == b'\x00':
        position -= 1
    audioEnd.append(position)
    # DEBUG
    if debug:
        with open(debugFile,'a') as f:
            f.write('\nBOUNDARIES - first valid - last valid byte offset:\n')
            for count, item in enumerate(audioStart):
                f.write(str(count)+' '+str(item)+'-'+str(audioEnd[count])+'\n')
    # END
    return zip(audioStart, audioEnd)

def formAudioParts(boundaries, data, debugFile):
    # DEBUG
    if debug:
        with open(debugFile,'a') as f:
            f.write('\nAUDIO PARTS - first valid - last valid byte offset:\n')
    # END
    audioParts = []
    for item in boundaries:
        temp = []
        start, end = item
        index = start
        while index + (2*chunkSize) < end:
            temp.append(data[index:index+chunkSize])
            # DEBUG
            if debug:
                with open(debugFile,'a') as f:
                    f.write(str(index)+'-'+str(index+chunkSize)+'\n')
            # END
            index += 2*chunkSize
        index -= chunkSize
        temp.append(data[index:end+1])
        # DEBUG
        if debug:
            with open(debugFile,'a') as f:
                f.write(str(index)+'-'+str(end-1)+'\n')
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

    start = findAudioStart(data)
    sys.stdout.write('\t\t\t[x] locating zero blocks.\r')
    fileSize, zeroBlocks = getZeroBlocks(data, debugFile)
    sys.stdout.write('\n\t\t\t[x] locating audio boundaries.')
    boundaries = locateBoundaries(zeroBlocks, start, fileSize, debugFile)
    sys.stdout.write('\n\t\t\t[x] gathering audio parts.')
    #audioBlocks = getAudioBlocks(zeroBlocks, data, start, fileSize, debugFile)
    audioBlocks = formAudioParts(boundaries, data, debugFile)
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
runningTimeTotal = str(round(time.time()-nowTotal,1))+' seconds.\n'
sys.stdout.write('\n'+filesTotal+' files overall processed in: '+runningTimeTotal)
input('<ENTER>')