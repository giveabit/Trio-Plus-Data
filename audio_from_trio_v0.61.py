#!/usr/bin/env python3

# needs to be changed: 'data' should always hold complete file for consistency!

# ++++++++++++++++++++++++++++++++++++++++++++
# IMPORTS
# ++++++++++++++++++++++++++++++++++++++++++++
import sys, time, os
from glob import glob

# ++++++++++++++++++++++++++++++++++++++++++++
# GLOBALS
# ++++++++++++++++++++++++++++++++++++++++++++
offsetAudioDefault = 170800 #bytes
offsetFF = 127288 # always FF FF FF FF
chunkSize = 32768 #bytes
wavDir = 'Trio_wav_export'
headerFile = wavDir+'/header.bin'
trioFileExtension = '.tlsd'

# ++++++++++++++++++++++++++++++++++++++++++++
# DEBUG?
# ++++++++++++++++++++++++++++++++++++++++++++
debug = False
debugDir = 'debug'

# ++++++++++++++++++++++++++++++++++++++++++++
# FUNCTIONS
# ++++++++++++++++++++++++++++++++++++++++++++
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


def writeBytes(fileName, data):
    with open(fileName, 'ab') as f:
        f.write(data)

def findAudioStart(data, debugFile):
    buffer = data[offsetFF:offsetFF+4]
    start = 0
    # DEBUG
    if debug:
        with open(debugFile, 'w') as f:
            f.write('FF FF FF FF Block at '+str(offsetFF)+':\n')
            if not buffer == b'\xFF'*4:
                f.write('NOT FOUND!\n')
            else:
                f.write('ok.\n')
    # END
    buffer = data[offsetFF+4:]
    for index in range(len(buffer)):
        if not buffer[index:index+1] == b'\x00':
            start = index
            break
    if start:
        start = start+offsetFF+4
        # DEBUG
        if debug:
            with open(debugFile, 'a') as f:
               f.write('\nfirst non-zero at '+str(start)+' / '+str(hex(start))+'\n\n')
        # END
        if start > offsetAudioDefault:
            return data[offsetAudioDefault:] #audio really seems to start at 170800 bytes
        else:
            return data[start:] #in case overdub recorded in first part might start earlier
    else:
        print('WARNING: no audio start found!')
        return 0

            

def getZeroBlocks(data, debugFile):
    fileSize = len(data)
    zeroBlocks = []
    position = 0
    while position <= fileSize-chunkSize:
        if position % 100000 == 0:
            reportProgress(position, fileSize)

        buffer = data[position:position+chunkSize]

        if verifyZeroBlock(buffer):
            zeroBlocks.append(position)
            zeroBlocks.append(position+chunkSize)
            position += chunkSize
        else:
            position +=1
    # DEBUG
    if debug:
        temp = zeroBlocks
        it = iter(temp)
        temp = zip(it,it)
        with open(debugFile, 'a') as f:
            f.write('ZERO BLOCKS LIST:\n')
            for item in temp:
                f.write(str(item)+'\n')
    # END
    return fileSize, zeroBlocks

def verifyZeroBlock(buffer):
    if buffer == b'\x00'*chunkSize:
        return True
    else:
        return False

def reportProgress(position, total):
    progress = float(position/total)*100
    sys.stdout.write("progress: %.2f%%   \r" % (progress))
    sys.stdout.flush()

def getAudioBlocks(zeroBlocks, data, fileSize, debugFile):

    # push in the start element (0) and the end element so that
    # the list of start/end zero-parts becomes
    # instead a list of start/end of audio parts
    # (assuming everything __between__ the zero chunks has to be audio data)
    zeroBlocks.insert(0,0)
    zeroBlocks.append(fileSize)

    #re-name just to reflect the change
    audioBlocksTemp = zeroBlocks

    # after this line of code, 'audioBlocksTemp' will be a list of lists
    # containing the recorded parts of the song in form of
    # a 'start at data byte #' - 'end at data byte #' list
    # in case only one audio part is detected, it's a list
    # of exactly one list (we test on that later on!)

    audioBlocksTemp = detectNewSongParts(audioBlocksTemp, debugFile)


    # DEBUG
    if debug:
        margin = 4 # 4 bytes = 32 bits = 1 sample
        temp = zeroBlocks
        it = iter(temp)
        temp = zip(it,it)
        with open(debugFile, 'a') as f:
            f.write('\n\nAUDIO BLOCK LIST:\n')
            foo = 0
            for item in temp:
                start, end = item
                if not (chunkSize-margin <= end-start <= chunkSize+margin):
                    f.write(str(foo)+'.'+str(item)+'\t\t\t*-*-*->'+str(end-start)+'\n')
                else:
                    f.write(str(foo)+'.'+str(item)+'\t\t'+str(end-start)+'\n')
                foo += 2
    # END

    audioBlocks = []
    # now for the final step, assignment of the actual audio data
    # to the final 'audioBlocks' list - we've been coming a long way until here!
    if len(audioBlocksTemp) > 1: #i.e.: we have a list of lists
        # DEBUG
        if debug:
            foo = 0
            with open(debugFile, 'a') as f:
                f.write('\nPARTS:')
                for part in audioBlocksTemp:
                    f.write('\n'+str(foo)+'.'+str(part))
                    foo += 1
        # END
        for part in audioBlocksTemp:
            iterator = iter(part)
            part = zip(iterator, iterator)
            temp = []
            for item in part:
                start, end = item
                temp.append(data[start:end])
            audioBlocks.append(temp)
    else: # list of exactly one list
        audioBlocksTemp = audioBlocksTemp[0] #unpack for iterator zipping!!!
        iterator = iter(audioBlocksTemp)
        audioBlocksTemp = zip(iterator, iterator)
        temp = []
        for item in audioBlocksTemp:
            start, end = item
            temp.append(data[start:end])
        audioBlocks.append(temp)
    return audioBlocks #needs to be a list of list(s)
    # this is now the binary audio information

def detectNewSongParts(audioBlocksTemp, debugFile):
    margin = 8 #bytes = 2 samples
    # 4 bytes = 32 bits = 1 sample
    # unfortunately this was not enough so I have tried a higher value hier
    audioBlocks=[]
    marker = []
    for index in range(0,len(audioBlocksTemp),2):
        lenght = audioBlocksTemp[index+1]-audioBlocksTemp[index]
        if lenght < chunkSize-margin and index+2 < len(audioBlocksTemp):# and statement: does not matter if very last audio block is shorter than expected. File simply ends...
            marker.append(index+2)
            # last index to include in the new 'audioBlocks' List
            # since list slice includes only start...end-1 (!)

        if lenght > chunkSize+margin:
            if lenght > 2 * chunkSize:  # ...a HUGE block is likely to be separate part on it's own
                if index > 0:                
                    marker.append(index)
                    marker.append(index + 2)
                else:
                    marker.append(index + 2)
            else:                       #...whereas a modest bigger chunk might only indicate a new part's beginning
                if not index in marker and not index+2 == len(audioBlocksTemp):                
                    marker.append(index)

    if marker:
        # DEBUG
        if debug:
            with open(debugFile, 'a') as f:
                f.write('\nMARKER:\n')
                foo = 0
                for item in marker:
                    f.write(str(foo)+'.'+str(item)+'\n')
                    foo += 1
        # END
        audioBlocks.append(audioBlocksTemp[0:marker[0]])
        for index in range(len(marker)):
            if not index == len(marker)-1:
                audioBlocks.append(audioBlocksTemp[marker[index]:marker[index+1]])
            else:
                audioBlocks.append(audioBlocksTemp[marker[index]:])
    else:
        #return audioBlocksTemp would not work as we need to return a list of list(s)
        audioBlocks.append(audioBlocksTemp[:])


    return audioBlocks


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

# ++++++++++++++++++++++++++++++++++++++++++++
#              M    A    I    N
# ++++++++++++++++++++++++++++++++++++++++++++
fileList = init()

for fileName in fileList:
    print('\nprocessing: '+fileName)
    now = time.time()
    data = readBytes(fileName, 0)

    if debug:
        debugFile = debugDir+'/'+fileName+'.DBG.txt'
    else:
        debugFile = None        
    
    data = findAudioStart(data, debugFile)
    fileSize, zeroBlocks = getZeroBlocks(data, debugFile)
    audioBlocks = getAudioBlocks(zeroBlocks, data, fileSize, debugFile)


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
        foo += 1


    runningTime = str(round(time.time()-now,1))+' seconds'
    print('\nthis took: '+runningTime)
input('\nend.')