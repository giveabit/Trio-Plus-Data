# v0.8 for Trio GUI

if __name__ == '__main__':
    """not meant to be called from outside"""
    foo= input('this module is part of \'The Trio GUI Tool\' and cannot be run alone <return>')
    quit()

import sys
import os
from glob import glob
import itertools
import ntpath
import pyaudio

# GLOBALS
offsetAudio = 138032  # bytes
chunkSize = 32768 #bytes
trioFileExtension = '.tlsd'
editPrefix = 'EDIT_'
wavDir = 'Trio_wav_export'
headerFile = wavDir+'/header.bin'
rsc = 'resource_files/'
rsc_empty_song = rsc + 'template_empty_song.tlsd'
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

class Part(object):# <----------
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


def readBytes(fileName, offset=0): # <----------
    with open(fileName, 'rb') as f:
        f.seek(offset)
        buffer = f.read()
    return buffer

def getPartInfo(data, debugFile=''): # <----------
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

def outFile(fileName, writeBytes):
    """APPEND ONLY"""
    with open(fileName, 'ab') as f:
        f.write(writeBytes)
    return

# ~~~~~~~~~~~~~~~~~ AUDIO FUNCTIONS ~~~~~~~~~~~~~~~~~~~~~
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


    new = []
    for part in parts:
        if not part.get_trained():
            new.append(part)
    return new

def write_wave_files(fileName, audioBlocks):
    errors = []
    if not os.path.isdir(wavDir):
        os.mkdir(wavDir)
    foo = 0
    # fileName = os.path.basename(fileName)
    for part in audioBlocks:
        if len(audioBlocks) > 1:
            outFileName = wavDir + '/' + fileName.split('.')[0] + '_' + str(foo) + '.tmp'
        else:
            outFileName = wavDir + '/' + fileName.split('.')[0] + '.tmp'
        for audioData in part:
            outFile(outFileName, audioData)  # first write all the plain audio data

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
            # ---> catch errors within Trio.GUI !!!!
            e = sys.exc_info()[0]
            errors.append(e)
            if os.path.isfile(outFileName):
                os.remove(outFileName)
        foo += 1
    return errors

# ~~~~~~~~~~~~~~~~~ CREATE NEW .tlsd FUNCTIONS ~~~~~~~~~~~~~~
def build_new_file(full_outfile_name, containers, new_data):
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
        name = ntpath.basename(full_outfile_name).split('.')[0]
        new_data[1332:1340] = (0).to_bytes(8, 'little') # delete the 8-char word 'Template'
        lenght = len(name)
        new_data[1332:1332+lenght] = bytearray(name.encode())
    
    try:
        with open(full_outfile_name, 'wb') as f:
            f.write(new_data)
    except:
        return full_outfile_name
 
    return 0

def read_empty_template(from_dir):
    """read the empty template file to memory or return 0"""
    try:
        # will contain the empty .tlsd file template
        file_name = os.path.join(from_dir, rsc_empty_song)
        new_data = readBytes(file_name, 0)
        return(new_data)
    except:
        return 0

def check_filename_for_new_file(outfile_name, SCRIPT_DIR): # <----------
    """
    perform checks and return -> [error-code] or None
    checks if outfile_name alphanum/space -> ['alnum']
    is a 1...16 char -> ['min-max']
    with at least alnum 1 char -> ['min1']
    file must not exist -> ['found_file']
    """
    if len(outfile_name) < 17 and len(outfile_name) > 0:
        if all(x.isalnum() or x.isspace() for x in outfile_name):
            if not any(x.isalnum() for x in outfile_name):
                #print("\n-> Please input at least one alpabetical letter.\n")
                return 'min1'
        else:
            # print("\n-> Please input only alphabetical letters and spaces.\n")
            return 'alnum'
    else:
        # print("\n-> Please input at least 1 and up to 16 characters.\n")
        return 'minmax'
    
    outfile_name = os.path.join(SCRIPT_DIR, outfile_name)+'.tlsd'
    if os.path.isfile(outfile_name):
        # input('Sorry, but ->'+outfile_name+'<- already exists. Please choose another name. <OK>')
        return 'found_file'
    return None

def prepare_containers(all_info): # <----
    source_part_counter = 0
    containers = [PartCopyContainer() for i in range(5)]
    errors = []
    for dict_ in all_info:
        go = True
        try:
            data = readBytes(dict_['source_file'])
        except:
            errors.append('unable to open file: '+dict_['source_file'])
            go = False
        if go:
            parts = getPartInfo(data)
            source = dict_['source_part'] # 0...4
            destination = dict_['destination_part'] # 0...4
            source += 1
            destination += 1

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
            containers[source_part_counter].source_file = dict_['source_file']
            containers[source_part_counter].source_part = source
            containers[source_part_counter].target_part_number = destination
            
            # don't forget to increase counter            
            source_part_counter += 1
    
    return containers, errors

# ~~~~~~~~~~~~~~~~~ UPLOAD AUDIO FUNCTIONS ~~~~~~~~~~~~~~
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

def mix_waves(wave_file, audio_from_tlsd, widget, ratio_wave=50, operation='+', preview=False, makeup_gain=False):
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
    else:
        gain = 1.0

    # lenght matching
    wave = read_wave(wave_file)
    lenght_wave = len(wave)
    lenght_audio_tlsd = len(audio_from_tlsd)
    if lenght_wave < lenght_audio_tlsd:
        fill_zero = lenght_audio_tlsd - lenght_wave
        if not preview:
            widget.status('(Info): filling wave file data up with '+str(fill_zero)+' zero-bytes.') # message to GUI
        wave = bytearray(wave)
        wave.extend(b'\x00' * fill_zero)
    if lenght_wave > lenght_audio_tlsd:
        too_much = lenght_wave - lenght_audio_tlsd
        if not preview:
            widget.status('(Info): wave file is too big by '+str(too_much)+' bytes. Will be chopped.') # message to GUI

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

    for twobytes_a, twobytes_b in zip(wave_a, wave_b):
        progress = int((counter/lenght)*100)
        if progress % 10 == 0:
            outline = 'MIXING: '+str(progress)+' %' # message to GUI
            widget.toplevel.title(outline)          # message to GUI
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

def upload_wave(wav_file_name, tlsd_file_name, target_part_num, ratio, makeup_gain, out_dir, widget, PREVIEW=True):
    data = readBytes(tlsd_file_name)
    parts = getPartInfo(data)
    target = target_part_num

    audioParts = formAudioParts([parts[target]], data, True) #True = give au AND od no matter what
    
    for num, audioPart in enumerate(audioParts):
        # first element, are audio chunks
        # second element, are overdub audio chunks
        audioPart = b''.join(audioPart) # flatten the list
        audioParts[num] = audioPart

    if PREVIEW:
        # guess the correct audio or overdub for preview
        if len(audioParts) > 1:
            loudness_A = calculate_loudness(audioParts[0])
            loudness_B = calculate_loudness(audioParts[1])
            if loudness_A > loudness_B:
                audioPart = audioParts[0]
            else:
                audioPart = audioParts[1]
        
        preview = []
        # do the preview mix
        # 10 seconds hardcoded preview time!
        preview.append(b''.join(mix_waves(wav_file_name, audioPart, widget, ratio, '+', True, makeup_gain)))
        return preview
        preview_mix(item, 10)
    else:
    # finally do the full mix - always apply to au and od chunks
        mix = []
        error = ''
        if parts[target].has_overdub():
            for audioPart in audioParts:
                mix.append(b''.join(mix_waves(wav_file_name, audioPart, widget, ratio, '+', False, makeup_gain))) # mix au and od
        else:
            mix.append(b''.join(mix_waves(wav_file_name, audioParts[0], widget, ratio, '+', False, makeup_gain))) # just mix au

        try:
            audio_chunks = chunker(mix[0], chunkSize)
            if parts[target].has_overdub():
                overdub_chunks = chunker(mix[1], chunkSize) # get chunks from mix data
            else:
                overdub_chunks = chunker(audioParts[1], chunkSize) # get chunks from original data
        except:
            error = 'CRITCAL: something went wrong during access to the mix-list.'
            error += '\naborting. sorry. please report to: giveabit@mail.ru'
            return error, ''

        # some checks
        au_chunks_lenght = len(audio_chunks)
        od_chunks_lenght = len(overdub_chunks)
        if au_chunks_lenght > od_chunks_lenght:
            error = 'CRITCAL: au-chunks lenght > od-chunks lenght.'
            error += '\naborting. sorry. please report to: giveabit@mail.ru'
            return error, ''
        if od_chunks_lenght > au_chunks_lenght and od_chunks_lenght -1 != au_chunks_lenght:
            error = 'CRITCAL: od-chunks lenght > au-chunks lenght +1.'
            error += '\naborting. sorry. please report to: giveabit@mail.ru <enter>'
            return error, ''

        # form ovderub/audio interleave
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
        part_lenght = parts[target].byte_lenght
        if not mix_lenght == part_lenght:
            if mix_lenght > part_lenght:
                error = 'WARNING: mix_lenght > part_lenght:\n'+ str(mix_lenght) + '>' + str(part_lenght)
                error += '\n...truncate and continue anyway. Result may be unsatisfying.'
                au_od_interleave = au_od_interleave[:part_lenght]
            else:
                error = 'WARNING: mix_lenght < part_lenght:\n' + str(mix_lenght) + '<' + str(part_lenght)
                error += '\n...continue anyway. Result may be unsatisfying.'
                # do nothing here on purpose!

        # fill mix values into memory and write new .tlsd file!
        start, end = parts[target].get_reserved_audio_space()
        data = bytearray(data)
        data[start:end] = au_od_interleave

        if not ntpath.basename(tlsd_file_name).startswith('upload_'):
            out_fileName = os.path.join(out_dir, 'upload_' + ntpath.basename(tlsd_file_name))
        else:
            out_fileName = os.path.join(out_dir, ntpath.basename(tlsd_file_name))

        with open(out_fileName, 'wb') as f:
            f.write(data)
        return error, out_fileName
