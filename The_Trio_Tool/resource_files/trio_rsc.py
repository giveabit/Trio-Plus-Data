

if __name__ == '__main__':
    main()
    """not meant to be called from outside"""
    foo= input('this module is part of \'The Trio Tool\' and cannot be run alone <return>')
    quit()

import time
import sys
import os
from resource_files.mod_interactive_input import ask
from glob import glob
import itertools

# GLOBALS
offsetAudio = 138032  # bytes
chunkSize = 32768 #bytes
trioFileExtension = '.tlsd'
editPrefix = 'EDIT_'
wavDir = 'Trio_wav_export'
headerFile = wavDir+'/header.bin'
rsc = 'resource_files/'
rsc_file = rsc+'program_defaults.ini'
rsc_empty_song = rsc+'template_empty_song.tlsd'
debugDir = 'Debug'
tlsd_dir = ''
dict_part_endings_dword = {1: 1300, 2: 1304, 3: 1308, 4: 1312, 5: 1316} # DWORD lenght
dict_part_infos = {1: 84272, 2: 95024, 3: 105776, 4: 116528, 5: 127280} # 5 DWORDs lenght / 20 bytes
# seems sufficient to take these 20 bytes - MAYBE MORE NECESSARY???
# [84272-84292]; [95024-95044]; [105776-105796]; [116258-116548]; [127280-127300]
# python-style: including first but excluding last element!
# first DWORD first byte 1 = part empty / 0 = part exists
# second DWORD = some value... 'trained'
# third DWORD FF FF FF FF = no Audio / == second DWORD: Audio
# ??? not always - forth DWORD first byte 1 = no OD / 0 = OD
# ??? not always - fifth DWORD first byte 1 = no OD / 0 = OD

dict_ext_part_infos ={1: 2352, 2: 18736, 3: 35120, 4: 51504, 5: 67888} # lenght: 16384 bytes

empty_part_bytes = b'\x01\x00\x00\x00\x00\x00\x00\x00\xff\xff\xff\xff\x00\x00\x00\x00\x00\x00\x00\x00' # 20 bytes

fixed_value_eof_locations = [544, 632, 1320] # DWORD lenght
# filesizes:
# 544-548 eof

# eof-1192:
# 632-636
# 1320-1324

dict_part_eof_dword = {1: 1248, 2: 1256, 3: 1264, 4: 1272} # DWORD lenght; EOF-1192
# eof-1192 in parts:
# 1248-1252 pt. 1
# 1256-1260 cont. or pt. 2
# 1264-1268 cont. or pt. 3
# 1272-1276 cont. or pt. 4

# ~~~~~~~~~~~~~~~~~ GENERAL FUNCTIONS ~~~~~~~~~~~~~~~~~~~~~
class color:
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    DARKCYAN = '\033[36m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

class PartCopyContainer(object):
    """
    container to temporarily take data of exisiting parts of other files
    target_part_number initialised with 0 -> idientifier to throw away later
    vaild numbers shall be 1...5
    """

    def __init__(self, target_part_number = 0, audio_area_data = '', part_info = '', ext_part_info = '',
                    source_file = '', source_part = 0):
        self.target_part_number = target_part_number
        self.audio_area_data = audio_area_data
        self.part_info = part_info
        self.ext_part_info = ext_part_info
        self.source_file = source_file
        self.source_part = source_part

class Part(object):
    # all values are False or integer except time_lenght is float !!!
    # would need re-writing since python does not use getter/setter style!!!
    id_counter = 0

    def reset_counter():
        Part.id_counter = 0
        return

    def __init__(self, trained=False, start_audio=False,
                 end_audio=False, start_overdub=False,
                 end_overdub=False, start_reserved=False,
                 end_reserved=False, byte_lenght=0, time_lenght=0):
        Part.id_counter += 1
        self.__Part_number = self.id_counter
        self.__Trained = trained
        self.__Start_audio = start_audio
        self.__End_audio = end_audio
        self.__Start_overdub = start_overdub
        self.__End_overdub = end_overdub
        self.__Start_reserved = start_reserved
        self.__End_reserved = end_reserved
        self.byte_lenght = byte_lenght
        self.time_lenght = time_lenght

    def __str__(self):
        try:
            return 'part: '+str(self.__Part_number)+'; trained: '+str(int.from_bytes(self.__Trained, byteorder='little'))\
                    + '; start: '+str(self.__Start_audio)+'; end: '+str(self.__End_audio) \
                    + '; od-start: ' + str(self.__Start_overdub) + '; od-end: ' + str(self.__End_overdub) \
                    + '; reserved-start: ' + str(self.__Start_reserved) + '; reserved-end: '\
                    + str(self.__End_reserved)
        except:
            return 'part: '+str(self.__Part_number)+'; trained: '+str(self.__Trained)\
                    + '; start: '+str(self.__Start_audio)+'; end: '+str(self.__End_audio) \
                    + '; od-start: ' + str(self.__Start_overdub) + '; od-end: ' + str(self.__End_overdub) \
                   + '; reserved-start: ' + str(self.__Start_reserved) + '; reserved-end: ' \
                   + str(self.__End_reserved)

    def get_part_number(self):
        return self.__Part_number

    def set_trained(self, value):
        if value:
            self.__Trained = value
        else:
            self.__Trained = False

    def get_trained(self):
        return self.__Trained

    def set_audio(self, start_offset, end_offset=False):
        if start_offset:
            self.__Start_audio = start_offset
        else:
            self.__Start_audio = False
        self.__End_audio = end_offset

    def get_audio(self, selector = ''):
        if selector == 'start':
            return self.__Start_audio
        elif selector == 'end':
            return self.__End_audio
        elif selector == '':
            return self.__Start_audio, self.__End_audio
        else:
            raise Exception('selector must be \'start\', \'end\' or left blank')

    def set_overdub(self, start_overdub, end_overdub=False):
        if start_overdub:
            self.__Start_overdub = start_overdub
        else:
            self.__Start_overdub = False
        self.__End_overdub = end_overdub

    def get_overdub(self, selector = ''):
        if selector == 'start':
            return self.__Start_overdub
        elif selector == 'end':
            return self.__End_overdub
        elif selector == '':
            return self.__Start_overdub, self.__End_overdub
        else:
            raise Exception('selector must be \'start\', \'end\' or left blank')

    def has_audio(self):
        if self.__Start_audio and self.__End_audio:
            return True
        else:
            return False

    def has_overdub(self):
        if self.__Start_overdub and self.__End_overdub:
            return True
        else:
            return False

    def set_reserved_audio_space(self, start, end):
        #the total reserved disk space from overdub start area (earliest beginning) until end
        self.__Start_reserved = start
        self.__End_reserved = end

    def get_reserved_audio_space(self):
        return self.__Start_reserved, self.__End_reserved

    def get_reserved_bytelenght(self):
        bytelenght = self.__End_reserved - self.__Start_reserved
        return bytelenght

def intro(mode=''):
    print('-----------------------------------------------------------------------------')
    print('|                                                 release-#: ---> 0.75 <--- |')
    print('|                                                                           |')
    print('|        ***************************                                 @@     |')
    print('|        ** MANIPULATE TLSD FILES **                                 @@     |')
    print('|        ** & EXTRACT AUDIO DATA  **                              @@@@@@@@  |')
    print('|        ***************************                                 @@     |')
    print('|                                                                    @@     |')
    print('| @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@     @@@      @@@@@@@@@@@@@              |')
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
    print()
    print('*** the Trio+ tool - giveabit@mail.ru ***')
    print('')
    if mode == 'c':
        print('MODE: CREATE A NEW .tlsd FILE')
    if mode == 'm':
        print('MODE: MODIFY A SINGLE .tlsd FILE')
    if mode == 'u':
        print('MODE: UPLOAD AUDIO')
    time.sleep(1)
def choose_mode():
    answer = ask('[e]xtract audio \n[m]anipulate single file\n\
[c]reate new file from existing parts\n\
[u]pload .wav-audio to a part\n\
[s]how info\n\nWhat shall we do?', mode, ['e', 'm', 'c', 'u', 's'], 5)
    return answer
def init():
    print('\nWelcome to the Trio+ tool!\n')
    print('You can either\n - extract recorded guitar tracks (extract Audio),')
    print(' - re-arrange the parts within one file (manipulate single file),')
    print(' - build a new .tlsd file from parts of other existing .tlsd files (create new)')
    print(' - upload .wav-audio to a trained/recorded/overdubbed part (upload)')
    print(' - show info on the parts within .tlsd files (show info)\n')
    read_ini()
    if debug:
        if not os.path.isdir(debugDir):
            os.makedirs(debugDir)
    fileList = []
    if len(sys.argv) == 2 and sys.argv[1][-5:] == '.tlsd': # file given with drag&drop
        try:
            file = os.path.basename(os.path.normpath(sys.argv[1]))
            fileList.append(file)
        except:
            print('\nWe encountered an error while processing: ')
            e = sys.exc_info()[0]
            print('The error message reads: ', e, '\n')
            input('<ok> - EXIT')
            sys.exit(-999)
        print('script started by drag&drop with: '+file)
        mode = choose_mode()
        if mode == 'e':
            if not os.path.isdir(wavDir):
                os.mkdir(wavDir)
        return fileList, debug, mode
    else:
        mode = choose_mode()
        if mode == 'm': # manipulate single file
            print('\n'*100)
            print('\nModify an existing .tlsd file. You can copy, move and erase parts.')
            print('Please choose a .tlsd file to edit!\n')
            file = fileDialog()
            while not file:
                print('\n'*100)
                intro('m')
                print('\nYoda says:\nFailed in your attempt to outsmart me you have!\n')
                print('-> choose a valid file number!\n')
                file = fileDialog()
            fileList.append(file)
        elif mode == 'c':  # create a new .tlsd with parts from other .tlsd files
            fileList = []
        elif mode == 'u': # upload audio to part
            print('\n'*100)
            print('\nUpload audio to a trained/recorded/overdubbed part.')
            print('Please choose a .tlsd file to edit!\n')
            file = fileDialog()
            while not file:
                print('\n'*100)
                intro('u')
                print('\nYoda says:\nFailed in your attempt to outsmart me you have!\n')
                print('-> choose a valid file number!\n')
                file = fileDialog()
            fileList.append(file)
            
        else:  # extract audio or show .tlsd info (hidden function)
            if tlsd_dir:
                fileList = glob(tlsd_dir+'/*' + trioFileExtension)
            else:
                fileList = glob('*' + trioFileExtension)
            if not fileList:
                print('sorry: no .tlsd files found in current directory. EXIT')
                input('<return>')
                sys.exit(-1)
            if not os.path.isdir(wavDir):
                os.mkdir(wavDir)
    return fileList, debug, mode
def read_ini():
    if os.path.isfile(rsc_file):
        config = []
        global debug
        global mode
        global tlsd_dir
        global makeup_gain
        with open(rsc_file, 'r') as f:
            temp = f.readlines()
            temp = temp[3:]
        for line in temp:
            try:
                config.append(line.split(':')[1].rstrip())
            except:
                print('error while processing config')
        if config[0] == '1':
            debug = True
        else:
            debug = False

        if config[1] == 'e':
            mode = 'e'
        elif config[1] == 'm':
            mode = 'm'
        elif config[1] == 'c':
            mode = 'c'
        elif config[1] == 'u':
            mode = 'u'
        elif config[1] == 's':
            mode = 's'

        if config[2]:
            if os.path.isdir(config[2]):
                tlsd_dir = config[2]
            else:
                tlsd_dir = ''
        else:
            tlsd_dir = ''

        if config[3] == '1':
            makeup_gain = True
        else:
            makeup_gain = False
        #print('dbg:',debug, 'mode', mode, 'dir:', tlsd_dir, 'gain:', makeup_gain, config[3])
        #input()
    else:
        print('no config found - ignoring!')
        debug = True
        mode = 'e'
        tlsd_dir = ''
        makeup_gain = True
        return 0
    return
def fileDialog(mode='trio'):
    """
    In MODE -trio- present and choose .tlsd files.
    
    In MODE -wav- present and choose .wav files.
    
    Success returns filename.
    
    Else returns 0.
    In MODE -wav- return -1 if no .wav files are present.
    """
    files = ''
    if mode == 'trio':
        if tlsd_dir:
            files = glob(tlsd_dir+'/*' + trioFileExtension)
        else:
            files = glob('*' + trioFileExtension)
    if mode == 'wav':
        files = glob('*.wav')
    if files:
        files.sort(key=lambda f: os.path.splitext(f)[1])
        for index, file in enumerate(files):
            print(index, '-', file)
        # file_number = input('\n\nPlease input file number for processing: ') - REMOVE
        file_number = ask('\n\nPlease input file number for processing: ', 0, list(range(len(files))), 6)
        # try: - REMOVE BLOCK!
        #     file_number = int(file_number)
        # except:
        #     return 0
        # if not file_number < len(files):
        #     return 0
        return files[file_number]
    if mode == 'trio':
        print('There are no '+trioFileExtension+' files in this folder')
        input('<ok> - EXIT')
        sys.exit(-999)
    if mode == 'wav':
        print('There are no .wav files in this folder')
        input('<ok>')
        return -1

def readBytes(fileName, offset):
    with open(fileName, 'rb') as f:
        f.seek(offset)
        buffer = f.read()
    return buffer
def getPartInfo(data, debugFile=''):
    Part.reset_counter()
    parts = [Part() for i in range(5)]  # create a list of 5 Part instances from 0...4
    offsetsTemp = []
    offsetsVerifiedStarts = []
    offsetsVerifiedEnds = []
    previous = offsetAudio
    part_counter = 0
    is_trained = False
    for i in range(1300, 1319, 4):
        if not data[i:i+4] == b'\x00' * 4:
            parts[part_counter].set_trained(int.from_bytes(data[i:i+4], byteorder='little'))
            is_trained = True
        part_counter += 1
    if not is_trained:
        # print('\t\t\t[-] no parts trained.')
        return parts

    # *************************
    # if debug and debugFile:
    #     with open(debugFile, 'a') as f:
    #         f.write('after raw part info\n')
    #         for part in parts:
    #             f.write(str(part)+'\n')

    for part in parts:
        if part.get_trained():
            start, overdub = findAudioStart(data, previous)
            end = part.get_trained() + previous
            if overdub:
                part.set_reserved_audio_space(start, end)
                # audio part starts later than overdub part ('start' refers to start of overdub)
                part.set_audio(start+chunkSize, end)
                # overdub starts first and so has to end earlier
                # beware: these are all assumptions!!!
                part_lenght = end - start
                full_chunks = int(part_lenght/chunkSize)
                if full_chunks % 2 == 0:
                    od_end = (full_chunks-1)*chunkSize+start
                    part.set_overdub(start, od_end)
                else:
                    od_end = full_chunks*chunkSize+start
                    part.set_overdub(start, od_end)
            else:
                part.set_reserved_audio_space(start - chunkSize, end)
                # audio part simply starts at 'start'
                part.set_audio(start, end)
            previous = end

            start, end = part.get_reserved_audio_space()
            part.byte_lenght = end-start
            part.time_lenght = round(part.byte_lenght/88200/2,1) # 88200 bytes per second with 16 bit/44,1 kHz ; /2 -> 2 audio's interleaved

    # *************************
    # if debug  and debugFile:
    #     with open(debugFile, 'a') as f:
    #         f.write('\nafter search start positions\n')
    #         for part in parts:
    #             f.write(str(part)+'\n')

    # verify the start positions
    count_contains_audio = 0
    for part in parts:
        if part.has_audio():
            count_contains_audio += 1
            start = part.get_audio('start')
            buffer = data[start:start+chunkSize]
            if verifyZeroBlock(buffer):
                part.set_audio(False, False)
                count_contains_audio -= 1
            if part.has_overdub():
                count_contains_audio += 1
                start = part.get_overdub('start')
                buffer = data[start:start + chunkSize]
                if verifyZeroBlock(buffer):
                    part.set_overdub(False, False)
                    count_contains_audio -= 1
    if not count_contains_audio:
        # print('\t\t\t[-] no parts recorded.')
        return parts

    # *************************
    # if debug and debugFile:
    #     with open(debugFile,'a') as f:
    #         f.write('\nafter verify start\n')
    #         for part in parts:
    #             f.write(str(part)+'\n')

    # verify endings
    for part in parts:
        start, end = part.get_audio()
        buffer = data[end-16:end]
        while buffer == b'\x00' * 16:
            end -= 16
            buffer = data[end-16:end]
        part.set_audio(start, end)
        if part.has_overdub():
            start, end = part.get_overdub()
            buffer = data[end - 16:end]
            while buffer == b'\x00' * 16:
                end -= 16
                buffer = data[end - 16:end]
            part.set_overdub(start, end)

    # *************************
    # if debug and debugFile:
    #     with open(debugFile, 'a') as f:
    #         f.write('\nafter verify end\n')
    #         for part in parts:
    #             f.write(str(part)+'\n')

    return parts
def exportTrioHeader(data, fileName):
    fileName = debugDir+'/'+fileName+'.header.bin'
    header = data[:offsetAudio]
    outFile(fileName, header)
def outFile(fileName, writeBytes):
    with open(fileName, 'ab') as f:
        f.write(writeBytes)
    return
def presentParts(parts):
    outstring = '|'
    for part in parts:
        outstring += '  PART '+str(part.get_part_number())+' |'
    print('=' * len(parts) * 10+'=')
    print(outstring)
    outstring='|'
    for part in parts:
        if part.get_trained():
            if part.has_overdub():
                outstring += ' overdub '
            elif part.has_audio():
                outstring += '   yes   '
            else:
                outstring += ' trained '
        else:
            outstring += '  empty  '
        outstring += '|'
    print(outstring)
    outstring='|'
    for part in parts:
        temp_str = str(part.time_lenght) + ' s'
        temp_lenght = len(temp_str)
        num_spaces = 9-temp_lenght
        if num_spaces % 2 == 0:
            outstring += ' ' * (int(num_spaces/2)) + temp_str + ' ' * (int(num_spaces/2))
        else:
            outstring += ' ' * (int(num_spaces/2) +1) + temp_str + ' ' * (int(num_spaces/2))
        outstring += '|'
    print(outstring)
    print('=' * len(parts) * 10+'=')

# ~~~~~~~~~~~~~~~~~ AUDIO FUNCTIONS ~~~~~~~~~~~~~~~~~~~~~
def old_A_XXXformAudioParts(parts, data, debugFile): #OLD CODE JUST FOR REFERENCE - NOT IN USE !!!
    # DEBUG
    if debug:
        with open(debugFile,'a') as f:
            f.write('\nAUDIO PARTS:\n')
    # END
    starts = []
    ends = []
    for part in parts:
        if part.has_audio():
            starts.append(part.get_audio('start'))
            ends.append(part.get_audio('end'))
        if part.has_overdub():
            starts.append(part.get_overdub('start'))
            ends.append(part.get_overdub('end'))
    all_audio_addresses = zip(starts, ends)

    audioParts = []
    for item in all_audio_addresses:
        temp = []
        start, end = item
        index = start
        while index + chunkSize < end:
            temp.append(data[index:index+chunkSize])
            # DEBUG
            if debug:
                with open(debugFile,'a') as f:
                    #f.write('~ '+str('{0:,}'.format(index))+' - '+str('{0:,}'.format(index+chunkSize))+'\n')
                    f.write('~ ' + str(index) + ' - ' + str(index + chunkSize) + '\n')
            # END
            index += 2*chunkSize
        # nonsense: index += chunkSize
        temp.append(data[index:end])
        # DEBUG
        if debug:
            with open(debugFile,'a') as f:
                #f.write('x '+str('{0:,}'.format(index))+' - '+str('{0:,}'.format(end-1))+'\n')
                f.write('x ' + str(index) + ' - ' + str(end - 1) + '\n')
                f.write('-'*30+'\n')
        # END
        audioParts.append(temp)
    return audioParts

def old_B_xxxformAudioParts(parts, data, debugFile):  #OLD CODE JUST FOR REFERENCE - NOT IN USE !!!
    # DEBUG
    if not debugFile:
        debug = False # THIS OVERRIDE IS UGLY - whole debug system needs re-writing!
    if debug:
        with open(debugFile, 'a') as f:
            f.write('\nAUDIO PARTS:\n')
    # END
    audioParts = []
    for part in parts:
        if part.has_audio():
            start, end = part.get_reserved_audio_space()
            part_lenght = end - start
            full_chunks = int(part_lenght / chunkSize)
            if not full_chunks % 2 == 0:
                full_chunks += 1
            full_chunks = int(full_chunks / 2)
            #*************************
            if debug:
                with open(debugFile, 'a') as f:
                    f.write('\n'+'~' * 80 + '\n')
                    f.write('part chunks info - part: ' + str(part.get_part_number()) +
                            '; length: ' + str(part_lenght) + '; full chunks: ' + str(full_chunks) +
                            '/' + str(full_chunks*2) + ' of: ' + str(part_lenght / chunkSize)
                            + '\n')
                    audio_lenght = part.get_audio('end')-part.get_audio('start')
                    f.write('Audio lenght: ' + str(audio_lenght) +
                            '; length/chunk size: ' + str(audio_lenght/chunkSize) + '\n')
            temp_od = []
            temp_au = []
            end_od = False
            end_au = False
            dbg_od = []
            dbg_au = []

            for i in range(full_chunks):
                end = start + chunkSize

                if part.has_overdub():
                    if end > part.get_overdub('end') and not end_od:
                        end_od = True
                        end = part.get_overdub('end')
                        temp_od.append(data[start:end])
                        dbg_od.append([start, end])
                    elif not end_od:
                        temp_od.append(data[start:end])
                        dbg_od.append([start, end])

                start += chunkSize
                end = start + chunkSize

                if end > part.get_audio('end') and not end_au:
                    end_au = True
                    end = part.get_audio('end')
                    temp_au.append(data[start:end])
                    dbg_au.append([start, end])
                elif not end_au:
                    temp_au.append(data[start:end])
                    dbg_au.append([start, end])

                start += chunkSize

            # *************************
            if debug and not end_od:
                if part.has_overdub():
                    with open(debugFile, 'a') as f:
                        f.write('\n!!! Check: end_OD value not \'True\'. Should be: ' +
                                str(part.get_overdub('end')) + ' ; is: ' + str(end) + '\n')
            lack_audio = part.get_audio('end') - end
            if debug and not end_au and lack_audio:
                with open(debugFile, 'a') as f:
                    f.write('\n!!! Warning: end AU not reached. Should be: ' +
                            str(part.get_audio('end')) + ' but is: ' + str(end) +
                            ' (-' + str(lack_audio) +  ')\n')

            audioParts.append(temp_au)
            if part.has_overdub():
                audioParts.append(temp_od)

            # DEBUG
            if debug:
                if part.has_overdub():
                    write_debug_audioparts(debugFile, dbg_au, dbg_od)
                else:
                    write_debug_audioparts(debugFile, dbg_au)
            # END
    return audioParts

def formAudioParts(parts, data, return_both = False):
    '''
    return a list containing at least the audio-section of the given parts
    in case of overdub also return these
    in case that audio-section was empty return zerobytes
    '''
    audios_container = []
    for part in parts:
        start, end = part.get_reserved_audio_space()
        all_chunks = chunker(data[start:end], chunkSize)
        overdub_chunks = []
        audio_chunks = []
        position = start
        for count, item in enumerate(all_chunks):
            position += len(item)
            if len(item) == chunkSize:
                if count % 2 == 0:
                    overdub_chunks.append(item)
                else:
                    audio_chunks.append(item)
            else:
                if position == end:
                    if count % 2 == 0:
                        overdub_chunks.append(item)
                    else:
                        audio_chunks.append(item)
                else:
                    input('WARNING: possible audio chunk has been dropped. <enter>')

        audios_container.append(audio_chunks)
        if part.has_overdub() or return_both:
            audios_container.append(overdub_chunks)

    return audios_container

def write_debug_audioparts(debugFile, dgb_au, dbg_od=[]):
    with open(debugFile, 'a') as f:
        f.write('-' * 80 + '\n')
    previous_end = 0
    for foo, item in enumerate(dgb_au):
        start, end = item
        foo += 1
        if start - previous_end > 2* chunkSize:
            with open(debugFile, 'a') as f:
                f.write('au ' + str(foo) + ': ' + str(start) + ' - ' + str(end) + '\t\t\tlenght: ' +
                        str(end - start) + '\n')
        else:
            with open(debugFile, 'a') as f:
                f.write('au ' + str(foo) + ': ' + str(start) + ' - ' + str(end) + '\t\t\tlenght: ' +
                        str(end - start) + ' -\tdistance: ' + str(start - previous_end) + '\n')
                if (start - previous_end) < chunkSize:
                    f.write('\t\t\t!!!\tWARNING: DISTANCE LENGHT TOO SHORT\t!!!')
        previous_end = end

    previous_end = 0
    if dbg_od:
        for foo, item in enumerate(dbg_od):
            start, end = item
            foo += 1
            if start - previous_end > 2* chunkSize:
                with open(debugFile, 'a') as f:
                    f.write('od ' + str(foo) + ': ' + str(start) + ' - ' +
                            str(end) + '\t\t\tlenght: ' + str(end - start) + '\n')
            else:
                with open(debugFile, 'a') as f:
                    f.write('od ' + str(foo) + ': ' + str(start) + ' - ' + str(end) +
                            '\t\t\tlenght: ' + str(end - start) + ' -\tdistance: ' +
                            str(start - previous_end) + '\n')
                    if (start - previous_end) < chunkSize:
                        f.write('\t\t\t!!!\tWARNING: DISTANCE LENGHT TOO SHORT\t!!!')
            previous_end = end
        with open(debugFile, 'a') as f:
            f.write('-' * 80 + '\n')
    return


def writeHeader(sizeAudio):
    data = []
    # byte number x...y
    # 0...3
    data.append('RIFF'.encode())
    fileSize = sizeAudio+44-8 #file-fileSize (equals file-fileSize - 8); wav header = 44 bytes
    sampleRate = 44100
    numberChannels = 1
    bitsPerSample = 16
    byteRate = int(sampleRate*bitsPerSample*numberChannels/8)
    blockAlign = int(numberChannels*bitsPerSample/8)
    subChunk2Size = fileSize-44

    # 4...7
    data.append(fileSize.to_bytes(4,'little'))
    # 8...15
    data.append('WAVEfmt '.encode())
    # 16...19
    data.append((16).to_bytes(4,'little')) #Subchunk1Size    16 for PCM
    # 20...21
    data.append((1).to_bytes(2,'little')) #Type of format (1 is PCM)
    # 22...23
    data.append(numberChannels.to_bytes(2,'little')) #Number of Channels
    # 24...27
    data.append(sampleRate.to_bytes(4,'little')) #sample rate
    # 28...31
    data.append(byteRate.to_bytes(4,'little'))# byteRate = sample Rate * BitsPerSample * Channels/ 8
    # 32...33
    data.append(blockAlign.to_bytes(2,'little'))#BlockAlign= NumChannels * BitsPerSample/8
    # 34...35
    data.append(bitsPerSample.to_bytes(2,'little')) # BitsPerSample
    # 36...39
    data.append('data'.encode())
    # 40...43
    data.append(subChunk2Size.to_bytes(4,'little'))#data-block fileSize (equals file-fileSize - 44)
    # 44...end : audio data
    with open(headerFile, 'wb') as f:
        for item in data:
            f.write(item)
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
def give_parts_with_audio_only(parts):
    new = []
    for part in parts:
        if part.has_audio():
            new.append(part)
    return new
def give_trained_parts_only(parts):
    new = []
    for part in parts:
        if part.get_trained():
            new.append(part)
    return new
def give_not_trained_parts(parts):
    new = []
    for part in parts:
        if not part.get_trained():
            new.append(part)
    return new
# ~~~~~~~~~~~~~~~~~ MANIPULATION FUNCTIONS ~~~~~~~~~~~~~~
def choose_operation(file_name, parts, data):
    # print(color.GREEN+'\nNOTE: This part of the program ist BETA and results may not be satisfying'+color.END)
    print('\nNOTE: This part of the program ist BETA and results may not be satisfying')
    file_name = os.path.basename(file_name)
    if not file_name[:5] == editPrefix:
        outfile_name = editPrefix + file_name
    else:
        outfile_name = file_name
    answer = ''
    while not answer == 'x':
        success = 0
        answer = ask('[c]opy, [m]ove, [e]rase part or [u]pload audio? [x] will exit the tool ',
                     '', ['c', 'm', 'e', 'u', 'x'], 5)
        if answer == 'c':
            source, destination = tlsd_manipulation_user_input(parts, answer)
            if source and destination:
                success = copy_part(outfile_name, parts, data, source, destination)
                input('copy done. <return>')
        elif answer == 'm':
            source, destination = tlsd_manipulation_user_input(parts, answer)
            if source and destination:
                copy_part(outfile_name, parts, data, source, destination)
                data = readBytes(outfile_name, 0)
                parts = getPartInfo(data)
                success = erase_part(outfile_name, parts, data, source)
                input('move done. <return>')
        elif answer == 'e':
            source, destination = tlsd_manipulation_user_input(parts, answer)
            if source:
                success = erase_part(outfile_name, parts, data, source)
                input('erase done. <return>')
        elif answer == 'u':
            print('- NOT IMPLEMENTED YET -\n')
        if success:
            return outfile_name
    return 0

def tlsd_manipulation_user_input(parts, mode):
    # lots of user input and checks
    valid_source_parts = give_trained_parts_only(parts)
    valid_destiantion_parts = give_not_trained_parts(parts)
    if not valid_source_parts:
        if mode == 'c':
            print('\nsorry - no trained or audio parts to copy!')
        if mode == 'm':
            print('\nsorry - no trained or audio parts to move!')
        if mode == 'e':
            print('\nsorry - no trained or audio parts to erase!')
        return 0, 0
    if not valid_destiantion_parts and mode in ['c', 'm']:
        if mode == 'c':
            print('\nsorry - no non-trained (totally empty) parts as copy destination available!')
            print('You may need to erase one first.')
        if mode == 'm':
            print('\nsorry - no non-trained (totally empty) parts as move destination available!')
            print('You may need to erase one first.')
        return 0, 0
    valid_source_numbers = []
    for part in valid_source_parts:
        valid_source_numbers.append(part.get_part_number())
    presentParts(valid_source_parts)
    if mode == 'c':
        source = ask('source: which part number shall be copied? ', '', valid_source_numbers, 6)
    if mode == 'm':
        source = ask('source: which part number shall be moved? ', '', valid_source_numbers, 6)
    if mode == 'e':
        source = ask('source: which part number shall be erased? ', '', valid_source_numbers, 6)
    if mode in ['c', 'm']:
        valid_destination_numbers = []
        for part in valid_destiantion_parts:
            valid_destination_numbers.append(part.get_part_number())
        presentParts(valid_destiantion_parts)
        if mode == 'c':
            destination = ask('destination: copy to which empty part number? ',\
                        '', valid_destination_numbers, 6)
        if mode == 'm':
            destination = ask('destination: move to which empty part number? ',\
                        '', valid_destination_numbers, 6)
    if mode == 'e':
        destination = 0

    # question = color.BOLD+color.RED+'\n>>>\tcopy from part: '+str(source)+' to part: '\
    #           +str(destination)+' ?\t<<<'+color.END
    if mode == 'c':
        question = '\n>>>\tcopy from part: '+str(source)+' to part: '\
                +str(destination)+' ?\t<<<'
    if mode == 'm':
        question = '\n>>>\tmove from part: '+str(source)+' to part: '\
                +str(destination)+' ?\t<<<'
    if mode == 'e':
        question = '\n>>>\terase part: ' + str(source) + ' ?\t<<<'
    answer = ask(question, 'yes', '', 1)
    if not answer:
        return 0, 0
    else:
        return source, destination


def copy_part(outfile_name, parts, data, source, destination):
    new_data = []
    new_file_lenght = offsetAudio

    # 0 -- AUDIO AREA -- INCLUDE RESERVED PARTS
    # ('trained' also means area is reserved on disk like if audio was actually recorded)
    for part in parts:
        current_part = part.get_part_number()
        if current_part == destination:
            start, end = parts[source-1].get_reserved_audio_space()
            # parts = list from 0...4 <-> part numbers = 1...5
            new_data.append(data[start:end])  # if no audio this should be zeroes
            new_file_lenght += end - start
        if part.get_trained():
            start, end = part.get_reserved_audio_space()
            new_data.append(data[start:end])  # if no audio this should be zeroes
            new_file_lenght += end - start

    # 1 -- CHANGE HEADER BYTES -- TRAINED PARTS
    header = bytearray(data[:offsetAudio])
    for part in parts:
        current_part = part.get_part_number()
        write_address = dict_part_endings_dword[current_part]
        if current_part == destination:
            source_lenght = parts[source-1].get_reserved_bytelenght()
            part.set_trained(source_lenght)
            insert_value = (source_lenght).to_bytes(4, byteorder='little')
            header[write_address:write_address+4] = insert_value

    # 2 -- CHANGE HEADER BYTES -- PART INFOS
    start = dict_part_infos[source]
    lenght = 20 # bytes / 5 DWORD values
    end = start + lenght
    insert_value = header[start:end]
    write_address = dict_part_infos[destination]
    header[write_address:write_address+lenght] = insert_value

    # 3 -- CHANGE HEADER BYTES -- EXTENDED PART INFOS
    start = dict_ext_part_infos[source]
    lenght = 16384 # bytes
    end = start + lenght
    insert_value = header[start:end]
    write_address = dict_ext_part_infos[destination]
    header[write_address:write_address+lenght] = insert_value

    # 4 -- ACCOUNT FOR NEW FILE LENGHT IN HEADER --
    # A) fixed values:
    first = True
    for write_address in fixed_value_eof_locations:
        if first:
            first = False
            insert_value = new_file_lenght.to_bytes(4, 'little')
            header[write_address:write_address + 4] = insert_value
        else:
            insert_value = (new_file_lenght - 1192).to_bytes(4, 'little')
            header[write_address:write_address + 4] = insert_value

    # B) part based values
    previous_value = offsetAudio-1192
    for part_number in dict_part_eof_dword:
        write_address = dict_part_eof_dword[part_number]
        if parts[part_number-1].get_trained():
            add_value = parts[part_number-1].get_trained()
            insert_value = (previous_value + add_value).to_bytes(4, 'little')
            header[write_address:write_address+4] = insert_value
            previous_value += add_value
        else:
            insert_value = (previous_value).to_bytes(4, 'little')
            header[write_address:write_address+4] = insert_value

    # 5 -- INSERT HEADER AS FIRST ELEMENT --
    header = bytes(header)
    new_data.insert(0, header)

    # 6 -- WRITE TO DISK / ERASE IF EXISTS --
    if os.path.isfile(outfile_name):
        os.remove(outfile_name)
    for item in new_data:
        outFile(outfile_name, item)
    else:
        return 1
def erase_part(outfile_name, parts, data, source):
    new_data = []
    new_file_lenght = offsetAudio

    # AUDIO AREA - INCLUDE RESERVED PARTS
    # ('trained' also means area is reserved on disk like if audio was actually recorded)
    for part in parts:
        current_part = part.get_part_number()
        if part.get_trained() and not current_part == source:
            start, end = part.get_reserved_audio_space()
            new_data.append(data[start:end])  # if no audio this should be zeroes
            new_file_lenght += end - start

    # CHANGE HEADER BYTES - TRAINED PARTS
    header = bytearray(data[:offsetAudio])
    for part in parts:
        current_part = part.get_part_number()
        write_address = dict_part_endings_dword[current_part]
        if current_part == source:
            insert_value = (0).to_bytes(4, byteorder='little')
            header[write_address:write_address+4] = insert_value
            part.set_trained(False)

    # CHANGE HEADER BYTES - PART INFOS
    start = dict_part_infos[source]
    lenght = 20 # bytes / 5 DWORD
    insert_value = empty_part_bytes
    write_address = start
    header[write_address:write_address+lenght] = insert_value

    # CHANGE HEADER BYTES - EXTENDED PART INFOS
    # >>> TO DO: check if needed to write 'empty'
    # to theses parts
    # in case: set up 'empty' bytes for write

    # start = dict_ext_part_infos[source]
    # lenght = ...
    # insert_value = empty_EXTENDED_part_bytes
    # write_address = start
    # header[write_address:write_address+lenght] = insert_value

    # ACCOUNT FOR NEW FILE LENGHT IN HEADER
    # A) fixed values:
    first = True
    for write_address in fixed_value_eof_locations:
        if first:
            first = False
            insert_value = new_file_lenght.to_bytes(4, 'little')
            header[write_address:write_address + 4] = insert_value
        else:
            insert_value = (new_file_lenght - 1192).to_bytes(4, 'little')
            header[write_address:write_address + 4] = insert_value

    # B) part based values
    previous_value = offsetAudio-1192
    for part_number in dict_part_eof_dword:
        write_address = dict_part_eof_dword[part_number]
        if parts[part_number-1].get_trained():
            add_value = parts[part_number-1].get_trained()
            insert_value = (previous_value + add_value).to_bytes(4, 'little')
            header[write_address:write_address+4] = insert_value
            previous_value += add_value
        else:
            insert_value = (previous_value).to_bytes(4, 'little')
            header[write_address:write_address+4] = insert_value

    # INSERT HEADER AS FIRST ELEMENT
    header = bytes(header)
    new_data.insert(0, header)

    # WRITE TO DISK / ERASE IF EXISTS
    if os.path.isfile(outfile_name):
        os.remove(outfile_name)
    for item in new_data:
        outFile(outfile_name, item)
    return 1

# ~~~~~~~~~~~~~~~~~ CREATE NEW .tlsd FUNCTIONS ~~~~~~~~~~~~~~
def present_build_process(outfile_name, containers):    
    """present the progress of the building process of the new .tlsd file"""
    print('\n' * 100)
    print('\n\nYour new file: ->'+outfile_name+'<- looks like this, at the moment:\n')
    print('|'+'+' * 60+'|')
    for i in range(5):
        match = False
        for j in range(5):
            if containers[j].target_part_number == i + 1:
                match = True
                print('| PART', i + 1, ':\n| ->',
                  containers[j].source_file, '|| part', containers[j].source_part)
        if not match:
            print('| PART', i + 1, ': -> E M P T Y <-')
        print('|'+'+' * 60+'|')
    print('')


def build_new_file(outfile_name, containers, new_data):
    """
    form a new .tlsd file in memory based on the empty template file
    where 'containers' (list 0...4 of container objects) hold the raw data
    and 'new_data' contains the empty template file (binary data)
    """

    # delete non populated containers
    temp = []
    for container in containers:
        if container.target_part_number:
            temp.append(container)
    containers = temp

    # sort 'em
    containers.sort(key=lambda x: x.target_part_number)

    new_data = bytearray(new_data)
    new_filesize = offsetAudio
    for current_part_number in range(1,6):
        part_lenght = 0        
        match = []

        match = [x for x in containers if x.target_part_number == current_part_number]
        if match:
            match = match[0]
            new_data.extend(match.audio_area_data)
            new_filesize += len(match.audio_area_data)
            part_lenght = len(match.audio_area_data)
            # Extended part infos
            ext_part_info = match.ext_part_info
            write_address = dict_ext_part_infos[current_part_number]
            lenght = 16384 # bytes
            new_data[write_address:write_address+lenght] = ext_part_info

            # Part infos
            part_info = match.part_info
            write_address = dict_part_infos[current_part_number]
            lenght = 20 # bytes
            new_data[write_address:write_address+lenght] = part_info

        # Filesize parts 1...4
        if not current_part_number == 5:
            write_address = dict_part_eof_dword[current_part_number]
            insert_value = (new_filesize-1192).to_bytes(4, 'little')
            new_data[write_address:write_address+4] = insert_value

        # Part lenghts
        write_address = dict_part_endings_dword[current_part_number]
        insert_value = (part_lenght).to_bytes(4, 'little')
        new_data[write_address:write_address+4] = insert_value

        # EOFs
        first = True
        for write_address in fixed_value_eof_locations:
            if first:
                first = False
                insert_value = new_filesize.to_bytes(4, 'little')
                new_data[write_address:write_address + 4] = insert_value
            else:
                insert_value = (new_filesize - 1192).to_bytes(4, 'little')
                new_data[write_address:write_address + 4] = insert_value
        
        # Filename
        name = outfile_name.split('.')[0]
        new_data[1332:1340] = (0).to_bytes(8, 'little') # delete the 8-char word 'Template'
        lenght = len(name)
        new_data[1332:1332+lenght] = bytearray(name.encode())


    with open(outfile_name, 'wb') as f:
        f.write(new_data)
 
    return()

def read_empty_template():
    """read the empty template file to memory or abort script"""
    try:
        # will contain the empty .tlsd file template
        new_data = readBytes(rsc_empty_song, 0)
        return(new_data)
    except:
        print('\n' * 100)
        print('Oops! Expected the file:\n-> ' + rsc_empty_song +
              '\n...but could not locate it!')
        print('\nPlease download the latest release version of this script from GitHub, extract all files and try again.\n')
        input('<ok> - EXIT')
        sys.exit(-999)

def filename_for_new_file():
    """
    returns a max. 16 char alphanum/space filename with at least 1 alnum char
    checks if file exists and if so starts over
    """
    print('\nFirst we need a filename to write the new data.')
    outfile_name = ''
    while not outfile_name:
        outfile_name = input(
            '\nPlease enter a filename\n(max. 16 alphanumeric characters with no file extension): ')
        if len(outfile_name) < 17 and len(outfile_name) > 0:
            if all(x.isalnum() or x.isspace() for x in outfile_name):
                if not any(x.isalnum() for x in outfile_name):
                    print("\n-> Please input at least one alpabetical letter.\n")
                    outfile_name = ''
            else:
                print("\n-> Please input only alphabetical letters and spaces.\n")
                outfile_name = ''
        else:
            print("\n-> Please input at least 1 and up to 16 characters.\n")
            outfile_name = ''
        if outfile_name:
            outfile_name += '.tlsd'
            if os.path.isfile(outfile_name):
                input('Sorry, but ->'+outfile_name+'<- already exists. Please choose another name. <OK>')
                outfile_name=''
    return(outfile_name)

def choose_sources_and_destinations():
    new_data = read_empty_template()
    # also inital check to prevent critical error (if missing)
    # happening late in the editing

    finish = 0
    source_part_counter = 0
    valid_destination_numbers = [1, 2, 3, 4, 5]
    containers = [PartCopyContainer() for i in range(5)]
    outfile_name = filename_for_new_file()
    
    print('\n-> OK, your new file will be created as:', outfile_name)

    while not finish:
        print('\n\nSOURCES - select a .tlsd file\n')
        source_file = fileDialog()
        while not source_file:
            print('\n'*100)
            intro('c')
            print('\nYoda says:\nFailed in your attempt to outsmart me you have!\n')
            print('-> choose a valid file number!\n')
            print('\n\nSOURCES - select a .tlsd file\n')
            source_file = fileDialog()
        data = readBytes(source_file, 0)
        parts = getPartInfo(data, None)
        if not parts:
            print('\nthere are no parts. Please choose another file')
            input('<return>')
        else:        
            print('\nSOURCE file:',source_file)
            print('Now select a part you want to copy to the new file:')
            valid_source_parts = give_trained_parts_only(parts)
            valid_source_numbers = []
            if valid_source_parts:
                for part in valid_source_parts:
                    valid_source_numbers.append(part.get_part_number())
                presentParts(valid_source_parts)
                source = ask('source: which part number shall be copied? ', '', valid_source_numbers, 6)

                # ... copy data from source file into container ...
                # A) audio area
                start, end = parts[source-1].get_reserved_audio_space()
                # parts = list from 0...4 <-> part numbers = 1...5
                audio_area_data = data[start:end]
               
                # B) part infos
                start = dict_part_infos[source]
                end = start + 20 # bytes / 5 DWORD values
                part_info = data[start:end]
                
                # C) further/extended part infos
                start = dict_ext_part_infos[source]
                end = start + 16384 # bytes
                ext_part_info = data[start:end]
                
                # D) populate object
                containers[source_part_counter].audio_area_data = audio_area_data
                containers[source_part_counter].part_info = part_info
                containers[source_part_counter].ext_part_info = ext_part_info
                containers[source_part_counter].source_file = source_file
                containers[source_part_counter].source_part = source



                present_build_process(outfile_name, containers)
                destination = ask('Destination part number: Coose an EMPTY part to place the source. ', '', valid_destination_numbers, 6)
                
                containers[source_part_counter].target_part_number = destination
                present_build_process(outfile_name, containers)
                
                # don't forget to increase counter            
                source_part_counter += 1
                # ...and update valid destinations
                valid_destination_numbers.remove(destination)

                
                
            else:
                print('\nsorry - no trained or audio parts in this file!')

            print('\nYou have selected',source_part_counter,' parts to copy into your file.')
            if source_part_counter < 5:
                answer = ask('Do you wish to add more parts?','yes')
                if not answer:
                    finish = True
                    print('\nWell then - let\'s create the new file...')
            else:
                print('\nAll 5 parts are full - will now create the new file...')
                finish = True
    build_new_file(outfile_name, containers, new_data)

# ~~~~~~~~~~~~~~~~~ UPLOAD AUDIO FUNCTIONS ~~~~~~~~~~~~~~

def handle_pyaudio_install():
    platform = sys.platform
    if platform == 'win32' or platform == 'win64':
        # windows
        command = 'python -m pip install pyaudio'
        
    elif platform == 'linux':
        # linux
        command = 'sudo apt-get install python3-pyaudio'
        
    elif platform == 'darwin':
        # macos x
        print('It seems you are running MacOS')
        print('You will have to install PyAudio manually')
        print('Please refer to:')
        print('https://stackoverflow.com/questions/33851379/pyaudio-installation-on-mac-python-3')
        input('OK <enter>')
        command = ''

    else:
        # FAIL
        command = ''
        print('OS could not be idientified - please install PyAudio manually.')
        input('Sorry! <enter>')

    if command:
        print('OS idientified as', platform)
        print('\nattempting package installation!')
        input('OK <enter>')
        os.system(command)

def try_pyaudio_import():
    global pyaudio
    try:
        import pyaudio ### !!!!!! ####
        PYAUDIO = True
    except ImportError:
        print('\n\nWarning: \'PyAudio\' could not be imported!')
        print('\nPyAudio is a python package that provides Bindings for PortAudio v19')
        print('- the cross-platform audio input/output stream library.')
        print('\nHere, it would provide a preview function if you wanted to upload')
        print('audio data to an existing part - you really would want this!')
        print('\nThe script will run without it but an install of PyAudio is recommended')
        answer = ask('\nShall we attempt to do an automatic install (internet connection needs to be enabled)?','yes')
        if not answer:
            PYAUDIO = False
            input('\nOK - we will contimue WITHOUT PyAudio <enter>')
        else:
            handle_pyaudio_install()
            try:
                import pyaudio ### !!!!!! ####
                PYAUDIO = True
                input('\n\nGreat! PyAudio has been installed and imported! <enter>')
            except ImportError:
                PYAUDIO = False
                input('Sorry but something went wrong <enter>')
    return PYAUDIO

def read_wave(filename):
    '''
    read wave data from filename
    return only the data part -> [44:]
    '''
    with open(filename, 'rb') as f:
        wave_data = f.read()
    return wave_data[44:]

def chunker(sequence, size):
    """Return the given SEQUENCE as a list of
    chunks with the defined SIZE.

    The last chunk may be smaller than SIZE.
    """
    return [sequence[pos:pos + size] for pos in range(0, len(sequence), size)]

def generator_chunks(chunks):
    '''
    yields one chunk per call
    '''
    for item in chunks:
        yield item

def check_clip(value):
    '''
    check if audio signal is within limits.
    if over max or under min value set to: max or min
    '''
    if value > 32767:
        value = 32767
    if value < -32768:
        value = -32768
    return value

def mix_waves(wave_file, audio_from_tlsd, ratio_wave=50, operation='+', preview=False):
    '''
    add or substract two 16 bit signed wave data
    return raw wave data (byte values) without header
    mixing stops at end of shortest input file (zip), thus wave_file will be extended with nullbytes if needed
    wave_file - must exist on HDD
    audio_from_tlsd - in form of one single big chunk - no 32 k chunks here!
    ratio_wave - how loud shall the wave data be mixed in
    '''
    ratio = ratio_wave
    ratio_2 = 100 - ratio
    ratio = ratio / 100
    ratio_2 = ratio_2 / 100
    if makeup_gain:
        gain = 1.5
        print('\n(Info): makeup gain will be applied - see: resource_files\program_defaults.ini\n')
    else:
        gain = 1.0
        print('\n(Info): makeup gain will NOT be applied - see: resource_files\program_defaults.ini\n')

    # lenght matching
    wave = read_wave(wave_file)
    lenght_wave = len(wave)
    lenght_audio_tlsd = len(audio_from_tlsd)
    if lenght_wave < lenght_audio_tlsd:
        fill_zero = lenght_audio_tlsd - lenght_wave
        print('(Info): filling wave file data up with',fill_zero,'zero-bytes.')
        wave = bytearray(wave)
        wave.extend(b'\x00' * fill_zero)
    if lenght_wave > lenght_audio_tlsd:
        too_much = lenght_wave - lenght_audio_tlsd
        print('(Info): wave file is too big by',too_much,'bytes. Will be chopped.')

    outline = 'prepairing...\r'
    print(outline, end='', flush=True)

    if preview:
        chop = 882000 # 10 seconds
        if lenght_audio_tlsd > chop:
            audio_from_tlsd=audio_from_tlsd[:chop+1]
        if lenght_wave > chop:
            wave = wave[:chop+1]

    # chunk raw data in 2 byte packs
    wave_a = chunker(wave, 2)
    wave_b = chunker(audio_from_tlsd, 2)
    if len(wave_a) < len(wave_b):
        lenght = len(wave_a)
    else:
        lenght = len (wave_b)
    counter = 0
    mix = []
    outline = '                            \r'
    print(outline, end='', flush=True)
    for twobytes_a, twobytes_b in zip(wave_a, wave_b):
        progress = int((counter/lenght)*100)
        if progress % 10 == 0:
            outline = 'mixing: '+str(progress)+' % \r'
            print(outline, end='', flush=True)
        # transform to signed integer
        int_a = int.from_bytes(twobytes_a, 'little', signed=True)
        int_b = int.from_bytes(twobytes_b, 'little', signed=True)
        # do the mixing: + or -
        if operation == '+':
            append_value = int(round(((ratio * int_a + ratio_2 * int_b)*gain), 0))
        else:
            append_value = int(round(((ratio * int_a - ratio_2 * int_b)*gain), 0))
        # just in case... avoid clipping
        append_value = check_clip(append_value)
        # re-transform to byte values
        append_value = append_value.to_bytes(2, 'little', signed=True)
        mix.append(append_value)
        # and we're done!
        counter +=1
    outline = '                                      \r'
    print(outline, end='', flush=True)
    return mix

def preview_mix(wave_data, seconds=10):
    bytelenght = 88200 * seconds      
    if len(wave_data) > bytelenght:
        wave_data = wave_data[:bytelenght+1]
    p = pyaudio.PyAudio()
    stream = p.open(format=p.get_format_from_width(2),
                    channels=1,
                    rate=44100,
                    output=True)
    stream.write(wave_data)
    stream.stop_stream()
    stream.close()
    p.terminate()

def calculate_loudness(wave_data):
    '''
    calculate the loudness of wave data
    '''
    # chunk raw data in 2 byte packs
    wave_data = chunker(wave_data, 2)
    int_wave = []
    for twobytes in wave_data:
        # transform to signed integer
        int_wave.append(int.from_bytes(twobytes, 'little', signed=True))
    positives = [z for z in int_wave if z>0]    
    sum_val = sum(positives)
    return sum_val