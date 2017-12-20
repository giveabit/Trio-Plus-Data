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

def modify_tlsd(fileList, debug):
    print('\nLegend:')
    print('trained\t= chord progression trained but no audio recorded')
    print('yes\t= audio has been recorded')
    print('overdub\t= additional audio overdub(s) have been recorded')
    fileName = fileList[0]
    while fileName:
        print('\nFile to edit:', fileName)
        print('\n\t\t\t[x] read song data.')
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

def extract_audio(fileList, debug):
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
                audioBlocks = formAudioParts(parts_with_audio, data)

                write_wave_files(fileName, audioBlocks)

        runningTime = str(round(time.time() - now, 1)) + ' seconds.\n'
        print('\t\t\t[x] finished in: ' + runningTime)
    runningTimeTotal = str(round(time.time() - nowTotal, 1)) + ' seconds.\n'
    sys.stdout.write('\n' + filesTotal + ' files overall processed in: ' + runningTimeTotal)
    input('<return>')

def write_wave_files(fileName, audioBlocks):
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
    return


def create_tlsd():
    print('\n'*100)
    print('Create a new .tlsd file from existing parts!\n\n')
    print('This will create a new .tlsd file that consists of parts')
    print('from other .tlsd files. You will be able to select up to 5 parts')
    print('from different source .tlsd files and put them in any order into')
    print('the newly created .tlsd file.\n')
    choose_sources_and_destinations()
    print('\nthat\'s it. EXIT')
    input('<return>')
    sys.exit(0)

def upload_audio(fileName):
    PYAUDIO = try_pyaudio_import()

    wavefile_list = glob('*.wav')
    while not wavefile_list:
        print('\n\nOOPS! No .wav files found!')
        print('Please make sure that your .wav file is in the same folder as this script!\n')
        answer = ask('Take your time and drop a .wav into the script folder... Try again?', 'yes')
        if answer:
            wavefile_list = glob('*.wav')
        else:
            input('ok - then we quit <enter>')
            exit()

    print('\n'*50)
    print('Upload to audio to an existing part.')
    print('The target part needs either to be marked as \'trained\', \'yes\' or \'overdub\'\n')
    print('*'*70)
    print('You may want to make sure that the wave-audio lenght')
    print('matches roughly the part lenght.')
    print('Upload will be \'chopped off\' if it is too long')
    print('\nAudio source _must_ be \'RIFF WAVE\' (.wav), 16 bit @ 44.1 kHz, mono')
    print('*'*70)

    data = readBytes(fileName, 0)
    print('\nyour file ->'+fileName+'<- looks like this:')
    parts = getPartInfo(data, None)
    presentParts(parts)
    trained_parts = give_trained_parts_only(parts)
    if not trained_parts:
        print('\n Sorry but you have no trained parts in your file. Please train a part first. You may also record audio to it.')
        input('quit <enter>')
        exit()
    print('\nplease choose a part to upload audio to:')
    presentParts(trained_parts)
    valid_target_numbers = []
    for part in trained_parts:
        valid_target_numbers.append(part.get_part_number())
    target = ask('upload audio to which part? ', str(valid_target_numbers[0]), valid_target_numbers, 6)

    print('\nChoose .wav file:')
    for num, wave_file in enumerate(wavefile_list):
        print(str(num) +':'+ wave_file)
    print()
    
    source = ask('which .wav-number would you like to upload? ', 0, list(range(len(wavefile_list))), 6)
    
    print('\n\nProbably you want your upload to be some kind of background pad-sound')
    print('Therefore a lower loudness ratio of ~20 % might be sufficient')
    print('If you have the pyaudio module installed you will be able to experiment with different ratios')
    ratio = ask('Loudness ratio of .wav file (0...100 %)',20,list(range(101)),6)
    
    print('\n-> Upload '+wavefile_list[source]+' to part number '+str(target)+' of '+fileName+'\n')
    answer = ask('Do it?', 'yes')
    if not answer:
        input('\n\nok - then we quit <enter>')
        exit()

    audioParts = formAudioParts([parts[target-1]], data, True) #True = give au AND od no matter what

    for num, audioPart in enumerate(audioParts):
        # first element, are audio chunks
        # second element, are overdub audio chunks
        audioPart = b''.join(audioPart) # flatten the list
        audioParts[num] = audioPart

    if PYAUDIO: # preview and correction loop
        print('Preparing audio preview.')

        # guess the correct audio or overdub for preview
        if len(audioParts) > 1:
            loudness_A = calculate_loudness(audioParts[0])
            loudness_B = calculate_loudness(audioParts[1])
            if loudness_A > loudness_B:
                audioPart = audioParts[0]
            else:
                audioPart = audioParts[1]
        proceed = False
        while not proceed:
            mix = []
            # do the preview mix
            # 10 seconds hardcoded preview time!
            mix.append(b''.join(mix_waves(wavefile_list[source], audioPart, ratio, '+', True)))
            for item in mix:
                print('10 seconds preview - outputting audio now...')
                preview_mix(item, 10)
            proceed = ask('proceed? y/n', 'yes')
            if not proceed:
                ratio = ask('Loudness ratio of .wav file (0...100 %)',
                            20, list(range(101)), 6)

    # finally do the full mix - always apply to au and od chunks
    mix = []
    if parts[target-1].has_overdub():
        for audioPart in audioParts:
            mix.append(b''.join(mix_waves(wavefile_list[source], audioPart, ratio, '+', False))) # mix au and od
    else:
        mix.append(b''.join(mix_waves(wavefile_list[source], audioParts[0], ratio, '+', False))) # just mix au

    try:
        audio_chunks = chunker(mix[0], chunkSize)
        if parts[target-1].has_overdub():
            overdub_chunks = chunker(mix[1], chunkSize) # get chunks from mix data
        else:
            overdub_chunks = chunker(audioParts[1], chunkSize) # get chunks from original data
    except:
        print('CRITCAL: something went wrong during access to the mix-list.')
        input('quitting. sorry. please report to: giveabit@mail.ru <enter>')
        exit()

    # some checks
    print('running checks.')

    au_chunks_lenght = len(audio_chunks)
    od_chunks_lenght = len(overdub_chunks)
    if au_chunks_lenght > od_chunks_lenght:
        print('CRITCAL: au-chunks lenght > od-chunks lenght.')
        input('quitting. sorry. please report to: giveabit@mail.ru <enter>')
        exit()
    if od_chunks_lenght > au_chunks_lenght and od_chunks_lenght -1 != au_chunks_lenght:
        print('CRITCAL: od-chunks lenght > au-chunks lenght +1.')
        input('quitting. sorry. please report to: giveabit@mail.ru <enter>')
        exit()

    # form ovderub/audio interleave
    print('weaving audio chunks.')

    au = generator_chunks(audio_chunks)
    od = generator_chunks(overdub_chunks)
    au_od_interleave = []
    while True:
        try:
            au_od_interleave.append(next(od))
        except StopIteration:
            break

        try:
            au_od_interleave.append(next(au))
        except StopIteration:
            break

    au_od_interleave = b''.join(au_od_interleave)

    # final check
    mix_lenght = len(au_od_interleave)
    part_lenght = parts[target-1].byte_lenght
    if not mix_lenght == part_lenght:
        if mix_lenght > part_lenght:
            print('WARNING: mix_lenght > part_lenght:', mix_lenght, '>', part_lenght)
            input('...truncate and continue anyway. Result may be unsatisfying. <enter>')
            au_od_interleave = au_od_interleave[:part_lenght]
        else:
            print('WARNING: mix_lenght < part_lenght:', mix_lenght, '<', part_lenght)
            input('...continue anyway. Result may be unsatisfying. <enter>')
            # do nothing here on purpose!

    # fill mix values into memory and write new .tlsd file!
    start, end = parts[target-1].get_reserved_audio_space()
    data = bytearray(data)
    data[start:end] = au_od_interleave

    out_fileName = 'upload_' + fileName
    outFile(out_fileName, data)

    print('\nYour new file has been sccessfully written as:', out_fileName)

    print('\nthat\'s it. EXIT')
    input('<return>')
    sys.exit(0)

def show_tlsd_info(fileList):
    for file in fileList:
        data = readBytes(file, 0)
        parts = getPartInfo(data)
        print('\ncurrent file: ', file)
        presentParts(parts)
        input('ok <enter>\n\n')
    print('\nthat\'s it. EXIT')
    input('<return>')

def main():
    intro()
    fileList, debug, mode = init()
    if mode == 'm': # manipulate single file
        modify_tlsd(fileList, debug)
    if mode == 'c': # create new .tlsd from parts of other .tlsd files
        create_tlsd()
    if mode == 'u':
        upload_audio(fileList[0])
    if mode == 's':
        show_tlsd_info(fileList)
    else: # exctract audio
        extract_audio(fileList, debug)

if __name__ == '__main__':
    main()
