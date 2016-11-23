#!/usr/bin/env python3

import sys, time, os
from glob import glob


offset = 170800 #bytes
chunkSize = 32768 #bytes
wavDir = 'Trio_wav_export'
headerFile = wavDir+'/header.bin'
trioFileExtension = '.tlsd'

debug = False

def init():
    if not os.path.isdir(wavDir):
        os.mkdir(wavDir)
    fileList = glob('*'+trioFileExtension)
    return fileList

def readBytes(fileName, offset):
    with open(fileName, 'rb') as f:
        f.seek(offset)
        buffer = f.read()
    return buffer


def writeBytes(fileName, data):
    with open(fileName, 'ab') as f:
        f.write(data)

def getZeroBlocks(data, debugFile=''):
    size = len(data)
    zeroBlocks = []
    position = 0
    while position <= size-chunkSize:
        if position % 100000 == 0:
            reportProgress(position, size)

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
        with open(debugFile, 'w') as f:
            f.write('Zero Block List:\n')
            for item in temp:
                f.write(str(item)+'\n')
    # END
    return size, zeroBlocks

def verifyZeroBlock(buffer):
    if buffer == b'\x00'*chunkSize:
        return True
    else:
        return False

def reportProgress(position, total):
    progress = float(position/total)*100
    sys.stdout.write("progress: %.2f%%   \r" % (progress))
    sys.stdout.flush()

def getAudioBlocks(zeroBlocks, data, size, debugFile=''):
    audioBlocks = []
    zeroBlocks.insert(0,0)
    if size-zeroBlocks[-1]>chunkSize:
        zeroBlocks.append(zeroBlocks[-1]+chunkSize)
    else:
        zeroBlocks.append(size)



    # DEBUG
    if debug:
        margin = 4 # 4 bytes = 32 bits = 1 sample
        temp = zeroBlocks
        it = iter(temp)
        temp = zip(it,it)
        with open(debugFile, 'a') as f:
            f.write('\n\nAudio Block List:\n')
            for item in temp:
                start, end = item
                if not (chunkSize-margin <= end-start <= chunkSize+margin):
                    f.write(str(item)+'\t\t\t*-*-*->'+str(end-start)+'\n')
                else:
                    f.write(str(item)+'\t\t'+str(end-start)+'\n')
    # END
    iterator = iter(zeroBlocks)
    zeroBlocks = zip(iterator, iterator)
    for item in zeroBlocks:
        start, end = item
        audioBlocks.append(data[start:end])
    return audioBlocks

def outFile(fileName, writeBytes):
    with open(fileName,'ab') as f:
        f.write(writeBytes)
    return
    
def writeHeader(sizeAudio):
    data = []
    data.append('RIFF'.encode())
    size = sizeAudio+44-8 #file-size (equals file-size - 8); wav header = 44 bytes
    sampleRate = 22050
    numberChannels = 1
    bitsPerSample = 32
    byteRate = int(sampleRate*bitsPerSample*numberChannels/8)
    blockAlign = int(numberChannels*bitsPerSample/8)
    subChunk2Size = size-44

    data.append(size.to_bytes(4,'little'))
    data.append('WAVEfmt '.encode())
    data.append((16).to_bytes(4,'little')) #Subchunk1Size    16 for PCM
    data.append((1).to_bytes(2,'little')) #Type of format (1 is PCM)    
    data.append(numberChannels.to_bytes(2,'little')) #Number of Channels 
    data.append(sampleRate.to_bytes(4,'little')) #sample rate
    data.append(byteRate.to_bytes(4,'little'))# byteRate = sample Rate * BitsPerSample * Channels/ 8 
    data.append(blockAlign.to_bytes(2,'little'))#BlockAlign= NumChannels * BitsPerSample/8
    data.append(bitsPerSample.to_bytes(2,'little')) # BitsPerSample   
    data.append('data'.encode())
    data.append(subChunk2Size.to_bytes(4,'little'))#data-block size (equals file-size - 44)
        
    with open(headerFile, 'wb') as f:
        for item in data: 
            f.write(item)

# ******************************************************
fileList = init()

for fileName in fileList:
    print('\nprocessing: '+fileName)
    now = time.time()


    data = readBytes(fileName, offset)

    if debug:
        size, zeroBlocks = getZeroBlocks(data, fileName+'.DBG.txt')
        audioBlocks = getAudioBlocks(zeroBlocks, data, size, fileName+'.DBG.txt')
    else:
        size, zeroBlocks = getZeroBlocks(data)
        audioBlocks = getAudioBlocks(zeroBlocks, data, size)

    outFileName = wavDir+'/'+fileName.split('.')[0]+'.tmp'
    for item in audioBlocks:
        outFile(outFileName,item)
    
    sizeAudio = os.path.getsize(outFileName)
    writeHeader(sizeAudio)
    
    try:
        with open(headerFile, "ab") as f1, open(outFileName, "rb") as f2:
            f1.write(f2.read())     
        wavFile = outFileName[:-3]+'wav'
        os.rename(headerFile, wavFile)
        os.remove(outFileName)
    except:
        e = sys.exc_info()[0]
        print(e)

    runningTime = str(round(time.time()-now,1))+' seconds'
    print('\nthis took: '+runningTime)
input('\nend.')