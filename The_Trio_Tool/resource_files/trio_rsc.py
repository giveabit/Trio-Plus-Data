
def main():
    pass

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

# GLOBALS
offsetAudio = 138032  # bytes
chunkSize = 32768 #bytes
trioFileExtension = '.tlsd'
editPrefix = 'EDIT_'
wavDir = 'Trio_wav_export'
headerFile = wavDir+'/header.bin'
rsc = 'resource_files/'
debugDir = 'Debug'
tlsd_dir = ''
dict_part_endings_dword = {1: 1300, 2: 1304, 3: 1308, 4: 1312, 5: 1316} # DWORD lenght
dict_part_infos = {1: 84272, 2: 95024, 3: 105776, 4: 116258, 5: 127280} # 5 DWORDs lenght
# [84272-84292]; [95024-95044]; [105776-105796]; [116258-116548]; [127280-127300]
# python-style: including first but excluding last element!
# first DWORD first byte 1 = part empty / 0 = part exists
# second DWORD = some value... 'trained'
# third DWORD FF FF FF FF = no Audio / == second DWORD: Audio
# ??? not always - forth DWORD first byte 1 = no OD / 0 = OD
# ??? not always - fifth DWORD first byte 1 = no OD / 0 = OD

empty_part_bytes = b'\x01\x00\x00\x00\x00\x00\x00\x00\xff\xff\xff\xff\x00\x00\x00\x00\x00\x00\x00\x00'

fixed_value_eof_locations = [544, 632, 1320]
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

class Part(object):
    # all values are False or integer !!!
    id_counter = 0

    def reset_counter():
        Part.id_counter = 0
        return

    def __init__(self, trained=False, start_audio=False,
                 end_audio=False, start_overdub=False,
                 end_overdub=False, start_reserved=False,
                 end_reserved=False):
        Part.id_counter += 1
        self.__Part_number = self.id_counter
        self.__Trained = trained
        self.__Start_audio = start_audio
        self.__End_audio = end_audio
        self.__Start_overdub = start_overdub
        self.__End_overdub = end_overdub
        self.__Start_reserved = start_reserved
        self.__End_reserved = end_reserved

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


def intro():
    print('-----------------------------------------------------------------------------')
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
    time.sleep(0.5)
def choose_mode():
    answer = ask('[e]xtract audio or [m]anipulate file?', mode, ['e', 'm'], 5)
    return answer
def init():
    print('\nWelcome!\n')
    read_ini()
    if debug:
        if not os.path.isdir(debugDir):
            os.makedirs(debugDir)
    fileList = []
    if len(sys.argv) == 2 and sys.argv[1][-5:] == '.tlsd':
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
        if mode == 'm':
            file = fileDialog()
            while not file:
                print('\n'*100)
                intro()
                print('\ninput error - try again!\n')
                file = fileDialog()
            fileList.append(file)
        else:
            if tlsd_dir:
                fileList = glob(tlsd_dir+'/*' + trioFileExtension)
            if not fileList:
                print('sorry: no .tlsd files found in current directory. EXIT')
                input('<return>')
                sys.exit(-1)
            if not os.path.isdir(wavDir):
                os.mkdir(wavDir)
    return fileList, debug, mode
def read_ini():
    rsc_file = rsc+'program_defaults.ini'
    if os.path.isfile(rsc_file):
        config = []
        global debug
        global mode
        global tlsd_dir
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
        else:
            mode = 'm'

        if config[2]:
            if os.path.isdir(config[2]):
                tlsd_dir = config[2]
            else:
                tlsd_dir = ''
        else:
            tlsd_dir = ''
        # print(debug, mode, tlsd_dir)
    else:
        print('no config found - ignoring!')
        debug = True
        mode = 'e'
        tlsd_dir = ''
        return 0
    return
def fileDialog():
    print()
    files = ''
    if tlsd_dir:
        files = glob(tlsd_dir+'/*' + trioFileExtension)
    if files:
        files.sort(key=lambda f: os.path.splitext(f)[1])
        for index, file in enumerate(files):
            print(index, '-', file)
        first = input('\n\nPlease input file number for processing:')
        try:
            first = int(first)
        except:
            return 0
        if not first < len(files):
            return 0
        return files[first]
    print('There are no '+trioFileExtension+' files in this folder')
    input('<ok> - EXIT')
    sys.exit(-999)
def readBytes(fileName, offset):
    with open(fileName, 'rb') as f:
        f.seek(offset)
        buffer = f.read()
    return buffer
def getPartInfo(data, debugFile):
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
    # if debug:
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

    # *************************
    # if debug:
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
    # if debug:
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
    if debug:
        with open(debugFile,'a') as f:
            f.write('\nafter verify end\n')
            for part in parts:
                f.write(str(part)+'\n')

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
    print('=' * len(parts) * 10+'=')

# ~~~~~~~~~~~~~~~~~ AUDIO FUNCTIONS ~~~~~~~~~~~~~~~~~~~~~
def XXXformAudioParts(parts, data, debugFile):
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

def formAudioParts(parts, data, debugFile):
    # DEBUG
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
    outfile_name = editPrefix + file_name
    answer = ''
    while not answer == 'x':
        success = 0
        answer = ask('[c]opy, [m]ove, [e]rase part or [u]pload audio? [x] will exit the tool ', '', ['c', 'm', 'e', 'u', 'x'], 5)
        if answer == 'c':
            success = copy_part(outfile_name, parts, data)
        elif answer == 'm':
            print('- NOT IMPLEMENTED YET -\n')
        elif answer == 'e':
            print('- NOT IMPLEMENTED YET -\n')
        elif answer == 'u':
            print('- NOT IMPLEMENTED YET -\n')
        if success:
            return outfile_name
    return 0
def copy_part(outfile_name, parts, data):
    # lots of user input and checks
    valid_source_parts = give_parts_with_audio_only(parts)
    valid_destiantion_parts = give_not_trained_parts(parts)
    if not valid_source_parts:
        print('\nsorry - no audio parts to copy!')
        return
    if not valid_destiantion_parts:
        print('\nsorry - no non-trained (totally empty) parts as copy destination available!')
        return
    valid_source_numbers = []
    for part in valid_source_parts:
        valid_source_numbers.append(part.get_part_number())
    presentParts(valid_source_parts)
    source = ask('source: which part number shall be copied? ', '', valid_source_numbers, 6)
    valid_destination_numbers = []
    for part in valid_destiantion_parts:
        valid_destination_numbers.append(part.get_part_number())
    presentParts(valid_destiantion_parts)
    destination = ask('destination: copy to which empty part number? ',\
                '', valid_destination_numbers, 6)
    # question = color.BOLD+color.RED+'\n>>>\tcopy from part: '+str(source)+' to part: '\
    #           +str(destination)+' ?\t<<<'+color.END
    question = '\n>>>\tcopy from part: '+str(source)+' to part: '\
               +str(destination)+' ?\t<<<'

    answer = ask(question, 'yes', '', 1)
    if not answer:
        return 0

    # ok let's do this!
    new_data = []
    new_file_lenght = offsetAudio

    # AUDIO AREA - INCLUDE RESERVED PARTS
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

    # CHANGE HEADER BYTES - TRAINED PARTS
    header = bytearray(data[:offsetAudio])
    for part in parts:
        current_part = part.get_part_number()
        write_address = dict_part_endings_dword[current_part]
        previous_value = offsetAudio
        if current_part == destination:
            if current_part == 1:
                add_value = parts[source-1].get_reserved_bytelenght()
                part.set_trained(previous_value+add_value)
                insert_value = (previous_value+add_value).to_bytes(4, byteorder='little')
            else:
                for foo in range(0, current_part-2 +1):
                    previous_value = parts[foo].get_trained() or previous_value
                    # parts = 0...4 <-> current_part = 1...5; minus another for previuous;
                    # plus one for range function
                add_value = parts[source-1].get_reserved_bytelenght()  # see above
                part.set_trained(previous_value+add_value)
                insert_value = (previous_value+add_value).to_bytes(4, byteorder='little')
            header[write_address:write_address+4] = insert_value
        elif current_part > destination and part.get_trained():
            for foo in range(0, current_part-2 +1):
                previous_value = parts[foo].get_trained() or previous_value
            add_value = part.get_reserved_bytelenght()
            part.set_trained(previous_value+add_value)
            insert_value = (previous_value+add_value).to_bytes(4, byteorder='little')
            header[write_address:write_address+4] = insert_value

    # CHANGE HEADER BYTES - PART INFOS
    start = dict_part_infos[source]
    end = start + 20 # 5 DWORD values
    insert_value = header[start:end]
    write_address = dict_part_infos[destination]
    header[write_address:write_address+20] = insert_value


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


    for item in new_data:
        outFile(outfile_name, item)
    input('done. <return>')
    return 1
def erase_part(parts, which, data):
    pass
def move_part(parts, source, destination, data):
    pass
def upload_audio(parts, file, data):
    pass

