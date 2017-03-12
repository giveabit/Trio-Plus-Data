# -*- coding: utf-8 -*-
#!/usr/bin/env python3


# IMPORTS
from resource_files.trio_rsc import *
import os


def debug_basic_tasks(data, fileName):
    fileName = os.path.basename(fileName)
    exportTrioHeader(data, fileName)
    debugFile = debugDir + '/' + fileName + '.DBG.txt'
    if os.path.isfile(debugFile):
        os.remove(debugFile)
    return debugFile

# MAIN
def main():
    intro()
    fileList, debug, mode = init()
    if mode == 'm':
        print('\nLegend:')
        print('trained\t= chord progression trained but no audio recorded')
        print('yes\t= audio has been recorded')
        print('overdub\t= additional audio overdub(s) have been recorded')
        print('\n\t\t\t[x] read song data.')
        fileName = fileList[0]
        while fileName:
            data = readBytes(fileName, 0)
            if debug:
                debugFile = debug_basic_tasks(data, fileName)
            else:
                debugFile = None
            print('\t\t\t[x] locating parts.')
            parts = getPartInfo(data, debugFile)
            if not parts:
                print('\nthere is nothing to do. EXIT')
                input('<return>')
                sys.exit(-1)
            presentParts(parts)
            fileName = choose_operation(fileName, parts, data)
        print('\nthat\'s it. EXIT')
        input('<return>')
        sys.exit(0)
    else:
        filesTotal = str(len(fileList))
        nowTotal = time.time()
        for fileName in fileList:
            print('\nprocessing: ' + fileName)
            now = time.time()
            data = readBytes(fileName, 0)
            if debug:
                debugFile = debug_basic_tasks(data, fileName)
            else:
                debugFile = None
            print('\t\t\t[x] locating parts.')
            parts = getPartInfo(data, debugFile)
            if parts:
                presentParts(parts)
                print('\t\t\t[x] gathering audio parts.')
                parts_with_audio = give_parts_with_audio_only(parts)
                if not parts_with_audio:
                    print('\t\t\t[ ] no audio recorded.')
                else:
                    audioBlocks = formAudioParts(parts_with_audio, data, debugFile)

                    print('\t\t\t[x] writing files.')
                    foo = 0
                    fileName = os.path.basename(fileName)
                    for part in audioBlocks:
                        if len(audioBlocks) > 1:
                            outFileName = wavDir + '/' + fileName.split('.')[0] + '_' + str(foo) + '.tmp'
                        else:
                            outFileName = wavDir + '/' + fileName.split('.')[0] + '.tmp'
                        for audioData in part:
                            outFile(outFileName, audioData)  # first write all the plain audio data
                        if not len(part):
                            print('\nWARNING: no Data for: ' + outFileName)

                        try:
                            sizeAudio = os.path.getsize(outFileName)  # we need the size to write a correct wav header
                            writeHeader(sizeAudio)  # do it!
                            with open(headerFile, "ab") as f1, open(outFileName, "rb") as f2:
                                f1.write(f2.read())  # now pump the data at the end of the header
                            wavFile = outFileName[:-3] + 'wav'
                            if os.path.isfile(wavFile):
                                os.remove(wavFile)
                            os.rename(headerFile, wavFile)  # rename nicely!
                            os.remove(outFileName)  # and clean up ;-)
                        except:
                            print('\nWe encountered an error while processing: ' + outFileName)
                            e = sys.exc_info()[0]
                            print('The error message reads: ', e, '\n')
                            if os.path.isfile(outFileName):
                                os.remove(outFileName)
                        foo += 1

            runningTime = str(round(time.time() - now, 1)) + ' seconds.\n'
            print('\t\t\t[x] finished in: ' + runningTime)
        runningTimeTotal = str(round(time.time() - nowTotal, 1)) + ' seconds.\n'
        sys.stdout.write('\n' + filesTotal + ' files overall processed in: ' + runningTimeTotal)
        input('<return>')

if __name__ == '__main__':
    main()

