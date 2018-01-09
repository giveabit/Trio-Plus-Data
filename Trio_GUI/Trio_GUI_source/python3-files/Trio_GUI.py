#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# The Trio+ Tool GUI

# - - - IMPORTS - - -
import sys
import os
from glob import glob
import ntpath
import tkinter as tk
from tkinter import messagebox
from tkinter import filedialog
import tkinter.font as tkFont

from PIL import Image, ImageTk  # pip install pillow
from resource_files.resources import Resources # Python Utilities file
import resource_files.trio_gui_rsc as trio

# XX XX XX BUNDLE DETECTION XX XX XX
if getattr(sys, 'frozen', False):
    # we are running in a bundle
    bundle_dir = sys._MEIPASS
else:
    # we are running in a normal Python environment
    bundle_dir = os.path.dirname(os.path.abspath(__file__))

# - - - CONSTANTS - - -
root = tk.Tk() # needs to go first!
CUSTOM_FONT = tkFont.Font(family="Helvetica", size=10)
CUSTOM_FONT_SMALL = tkFont.Font(family="Helvetica", size=8)

x_size = 1000  # px wide app
y_size = 635  # px hight app

SCRIPT_DIR = bundle_dir
# handle for resource files
res = Resources(os.path.join(SCRIPT_DIR, "resource_files"))

# list of all resource file pictures
pics = ['part_none.png', 'part_empty.png', 'part_trained.png', 'part_recorded.png',
                'part_overdub.png', 'part_none_active.png', 'part_empty_active.png',
                'part_trained_active.png', 'part_recorded_active.png', 'part_overdub_active.png',
                'open_folder.png', 'refresh.png', 'ok.png', 'cancel.png', 'save.png',
                'upload_wav.png', 'wav_export.png', 'beer.png', 'pf.png', 'err_file.png',
                'err_export.png','wait.png', 'cancel_big.png', 'err_upload.png',
                'preview.png']
# resolve full pathnames
pics = [res.get_path(pic) for pic in pics]

# convert to pyimage 
pyimages = [ImageTk.PhotoImage(Image.open(pic)) for pic in pics]

# dictionary key values
constants = ['none', 'empty', 'trained', 'recorded', 'overdub',
                'none', 'empty', 'trained', 'recorded', 'overdub',
                'IMG_OPEN', 'IMG_REFRESH', 'IMG_OK', 'IMG_CANCEL', 'IMG_SAVE',
                'IMG_UPLOAD', 'IMG_EXPORT', 'IMG_BEER', 'IMG_PETER', 'IMG_ERR_FILE',
                'IMG_ERR_EXPORT', 'IMG_WAIT', 'IMG_CANCEL_BIG', 'IMG_ERR_UPLOAD',
                'IMG_PREVIEW']

# dictionary creation; fill with values
PART_PICS = {}
PART_PICS_CLICKED = {}
PICS = {} # all other buttons-pics
for i in range(5):
    PART_PICS[constants[i]] = pyimages[i]
    PART_PICS_CLICKED[constants[i+5]] = pyimages[i+5]
for i in range(10, len(constants)):
    PICS[constants[i]] = pyimages[i]

# other constants
FAVICO = res.get_path('favicon.ico')
# FAVICO = None

EXT = '.tlsd'
BG_COLOR = '#ececec'

# - - - GLOBALS - - -
Full_Filenames = []
New_File_Name = ''

# - - - THE CLASS - - - 
class part_button(object):

    all_buttons_source = []
    all_buttons_target = []

    def __init__(self, button_number, destination, part_state, duration=0, full_filename=''):
        self.button_number = button_number
        self.destination = destination
        self.target_frame = self.return_target_frame(self.destination)
        self.part_state = part_state
        self.full_filename = full_filename
        self.duration = duration
        self.set_photo(PART_PICS)
        self.button = tk.Button(self.target_frame, borderwidth=0, command=lambda x=self.button_number: self.toggle_state(x), image=self.photo)
        self.button.image = self.photo  # attach to avoid garbage collection
        self.clicked = False
        self.part_number = False # used only for target parts; derived from source part button number

    def new_file_info():
        all_info = []
        for item in part_button.all_buttons_target:
            if item.part_state in ['trained', 'recorded', 'overdub']:
                info = {}
                info['source_file'] = item.full_filename
                info['source_part'] = item.part_number
                info['destination_part'] = item.button_number
                all_info.append(info)
        return all_info

    
    def return_target_frame(self, destination):
        if destination == 'source':
            return frm_source
        else:
            return frm_target

    def toggle_state(self, number):
        """
        toggle button state and picture
        impossible to un-select the same button by clicking again by design!
        note: Will also call copy_part() method if one source and one target buttons are 'clicked == True'
        """
        if self.destination == 'source':
            list_name = part_button.all_buttons_source
        else:
            list_name = part_button.all_buttons_target
        
        for item in list_name:
            # reset all to non-clicked
            item.clicked = False
            item.set_photo(PART_PICS)
            # now set the one as 'clicked'
            if item.button_number == number:
                item.clicked = True
                # and finally change picture
                item.set_photo(PART_PICS_CLICKED)   
            item.button.config(image=item.photo) # to avoid garbage collection!!!
        if any (item.clicked for item in self.all_buttons_source) and any (item.clicked for item in self.all_buttons_target):
            self.copy_part()

    def copy_part(self):
        for item in part_button.all_buttons_source:
            if item.clicked:
                source = item
                break

        for item in part_button.all_buttons_target:
            if item.clicked:
                item.full_filename = source.full_filename
                item.part_number = source.button_number
                item.part_state = source.part_state
                item.set_photo(PART_PICS_CLICKED)
                item.button.config(image=item.photo)
                item.duration = source.duration
                durations_target[item.button_number].config(text=str(item.duration)+' s')
                self.update_status()
                break
        self.reset(source.button_number, item.button_number)

    def reset(self, source_num, target_num):
        items = []
        items.append(part_button.all_buttons_source[source_num])
        items.append(part_button.all_buttons_target[target_num])
        for item in items:
            item.clicked = False
            item.set_photo(PART_PICS)
            item.button.config(image=item.photo)

    def update_status(self):
        out_string = 'New file details (\'?\' parts will automatically be treated as \'empty\' upon saving):\n\n'
        for n, item in enumerate(self.all_buttons_target):
            if item.part_state != 'empty':
                if item.full_filename:  
                    out_string += 'Part # '+str(n+1)+':\t'+ntpath.basename(item.full_filename)+'--> Part # '+str(item.part_number+1)+'\n'
                else:
                    out_string += 'Part # '+str(n+1)+':\t?\n'
            else:
                out_string +='Part # '+str(n+1)+':\tempty part\n'
        lbl_target_log.config(text=out_string.rstrip())

    def set_photo(self, pic_dict_name):
        self.photo = pic_dict_name[self.part_state]

    def __repr__(self):
        return '<%s %s - %s - %s - clicked: %s>\n--> <%s>' % (
        self.__class__.__name__, self.button_number, self.part_state, self.destination, self.clicked, self.full_filename)

# - - - Define root window - - -
x = int((root.winfo_screenwidth() - root.winfo_reqwidth()) / 2) - int(x_size / 2)
y = int((root.winfo_screenheight() - root.winfo_reqheight()) / 3) - \
    int(y_size / 3)
root.geometry("{}x{}+{}+{}".format(x_size, y_size, x, y))
root.title('Trio+ Tool GUI')
root.tk_setPalette(background=BG_COLOR)
root.iconbitmap(FAVICO)
root.minsize(width=x_size, height=y_size)
# root.wm_resizable(0, 0)

# - - - FRAMES - - -
opts = {'bg': BG_COLOR, 'bd': 3, 'padx': 5, 'pady': 5, 'relief': 'groove', }

# Files Section * Main *
frm_files = tk.Frame(root, **opts)
frm_files.grid(column=0, row=0, sticky='NSWE')  # <---
# Files Section ~ sub ~
frm_files_icons = tk.Frame(frm_files, **opts)
frm_files_icons.grid(column=1, row=0, sticky='E')

# Source & Target * Main *
frm_source_target = tk.Frame(root, **opts)
frm_source_target.grid(column=1, row=0, sticky='NSWE')  # <---
# Source Section ~ sub ~
frm_source = tk.Frame(frm_source_target, **opts)
frm_source.grid(column=0, row=0, sticky='WE')
# Target Section ~ sub ~
frm_target = tk.Frame(frm_source_target, **opts)
frm_target.grid(column=0, row=1, sticky='WE')

# ~sub~ source / export and upload wave
frm_exp_upload = tk.Frame(frm_source, **opts)
frm_exp_upload.grid(column=6, row=1, rowspan=2, sticky='WE')
frm_exp_upload.columnconfigure(0, minsize=150)

# ~sub~ target / enter filename
frm_enter_filename = tk.Frame(frm_target)
frm_enter_filename.grid(column=0, columnspan=6, row=3, sticky='WE')

# ~sub~ target / cancel and save new file
frm_cancel_save = tk.Frame(frm_target, **opts)
frm_cancel_save.grid(column=6, columnspan=2, row=1, rowspan=2, sticky='WE')
frm_cancel_save.columnconfigure(0, minsize=150)

# Status Section * Main *
frm_status = tk.Frame(root, **opts)
frm_status.grid(column=0, columnspan=2, row=1, sticky='WE')  # <---

# Status Section ~sub~
frm_beer= tk.Frame(frm_status)
frm_beer.grid(column=1, row=0)
frm_beer.columnconfigure(0, minsize=200)

# - - - BUTTON FUNCTIONS - - -

class popup_ok(object):
    """
    custom message window with <ok> button
    pause mainloop (root.wait_window)
    """
    def __init__(self, message, image, title='ERROR'):
        self.toplevel = tk.Toplevel(padx=30, pady=30)
        self.toplevel.title(title)
        self.toplevel.grab_set()
        self.toplevel.iconbitmap(FAVICO)
        self.toplevel.resizable(0,0)
        self.lbl_errpic = tk.Label(self.toplevel, image=image)
        self.lbl_errpic.image=image
        self.lbl_errpic.grid(column=0, row=0)
        self.lbl_message = tk.Label(self.toplevel, justify='left', font=CUSTOM_FONT, padx=10, pady=10)
        self.lbl_message.config(text=message)
        self.lbl_message.grid(column=1, row=0)
        self.but_ok = tk.Button(self.toplevel, bd=5, text='    OK    ', command=self.kill)
        self.but_ok.grid(column=0, columnspan=2, row=1)
        self.but_ok.focus_set()
        self.toplevel.bind('<Return>', lambda _: self.kill())
        root_x, root_y, dx, dy, w, h = window_positioning(self.toplevel)
        self.toplevel.geometry('{}x{}+{}+{}'.format(w, h, root_x + dx, root_y + dy))
        self.toplevel.update()
        self.toplevel.deiconify()
        root.wait_window(self.toplevel)

    def kill(self):
        self.toplevel.destroy()

class popup_wait(object):
    """
    custom wait message window with no buttons
    no pause mainloop (root.wait_window)
    can receive status messages from outside in lbl_status via 'status(->string)' method
    """
    def __init__(self, message, image=PICS['IMG_WAIT'], title='PLEASE WAIT'):
        self.toplevel = tk.Toplevel(padx=30, pady=30)
        self.toplevel.title(title)
        self.image = image
        self.message = message
        self.lbl_errpic = tk.Label(self.toplevel, image=self.image)
        self.lbl_errpic.image=image
        self.lbl_errpic.grid(column=0, row=0)
        self.lbl_message = tk.Label(self.toplevel, justify='left', font=CUSTOM_FONT, padx=10, pady=10)
        self.lbl_message.config(text=self.message)
        self.lbl_message.grid(column=1, row=0)
        self.lbl_status = tk.Label(self.toplevel, justify='left', anchor='w', font=CUSTOM_FONT_SMALL, padx=10, pady=10)
        self.lbl_status.grid(column=0, columnspan=2, row=1)
        self.toplevel.grab_set()
        self.toplevel.iconbitmap(FAVICO)
        self.toplevel.resizable(0,0)
        self.toplevel.protocol("WM_DELETE_WINDOW", self.disable_event)
        root_x, root_y, dx, dy, w, h = window_positioning(self.toplevel)
        self.toplevel.geometry('{}x{}+{}+{}'.format(w, h, root_x + dx, root_y + dy))
        self.toplevel.update()
        self.toplevel.deiconify()

    def status(self, message_text):
        self.lbl_status.config(text=message_text)
        self.toplevel.update()

    def generate():
        return self.toplevel

    def disable_event(self, *args):
        pass
    
    def kill(self):
        self.toplevel.destroy()

class upload(object):
    def __init__(self, wav_file_name, part_num, full_file_name):
        self.toplevel = tk.Toplevel(padx=30, pady=30)
        self.toplevel.attributes("-topmost", True)
        self.toplevel.title('Upload .wav to source part')
        self.image = PICS['IMG_ERR_UPLOAD']
        self.wav_file_name=wav_file_name
        self.part_num =part_num
        self.full_file_name=full_file_name

        # LABELS
        self.message = 'upload .wav file:\n'+ ntpath.basename(self.wav_file_name)+\
                    '\n\nto:\nPart # '+str(self.part_num+1)+' of '+ntpath.basename(self.full_file_name)+'\n\n'

        self.lbl_errpic = tk.Label(self.toplevel, image=self.image)
        self.lbl_errpic.image=self.image
        self.lbl_errpic.grid(column=0, row=0, sticky='W')

        self.lbl_message = tk.Label(self.toplevel, justify='left', font=CUSTOM_FONT, padx=10, pady=10)
        self.lbl_message.config(text=self.message)
        self.lbl_message.grid(column=1, row=0)

        self.lbl_preview = tk.Label(self.toplevel, justify='left', font=CUSTOM_FONT_SMALL)
        self.lbl_preview.config(text='Mix preview')
        self.lbl_preview.grid(column=3, row=1, sticky='WS')

        self.lbl_mixvol = tk.Label(self.toplevel, justify='left', font=CUSTOM_FONT_SMALL)
        self.lbl_mixvol.config(text='Mix volume (0...100 %)')
        self.lbl_mixvol.grid(column=1, row=1, sticky='WS')

        self.lbl_gain = tk.Label(self.toplevel, justify='left', font=CUSTOM_FONT_SMALL)
        self.lbl_gain.config(text='Apply gain (recommended: on)')
        self.lbl_gain.grid(column=2, row=1, sticky='WS')

        self.lbl_explain = tk.Label(
            self.toplevel, justify='left', font=CUSTOM_FONT)
        explain = 'Adjust the mix level.\nChoose makeup gain on/off.\nClick on the loudspeaker icon to hear a '
        explain += '10 second mix preview.\nRepeat until you\'re satisfied.\n\nFinally, click \'OK\' to apply the mix.\n\n'
        self.lbl_explain.config(text=explain)
        self.lbl_explain.grid(column=1, columnspan=2, row=3)

        # ENTRY
        self.e_mix_text = tk.StringVar()
        self.e_mix=tk.Entry(self.toplevel, width=3, bg='#FFFFFF', font=CUSTOM_FONT, textvariable=self.e_mix_text)
        self.e_mix.insert(0, 20)
        self.e_mix.grid(column=1, row=2, sticky='WN')
        self.e_mix.focus_set()
        self.e_mix_text.trace('w', lambda *args: self.validate(self.e_mix_text))

        #CHECKBUTTON
        self.gain_var=tk.IntVar()
        self.gain_var.set(1)
        self.chbut_gain=tk.Checkbutton(self.toplevel, variable=self.gain_var, command=self.cb)
        self.chbut_gain.grid(column=2, row=2, sticky='WN')

        # BUTTONS
        self.but_preview = tk.Button(self.toplevel, bd=5, image=PICS['IMG_PREVIEW'], command=self.play_preview)
        self.but_preview.image=PICS['IMG_PREVIEW']
        self.but_preview.grid(column=3, row=2, sticky='WN')

        self.but_ok = tk.Button(self.toplevel, bd=5, text='    OK    ', command=self.ok)
        self.but_ok.grid(column=1, row=4)
        
        self.but_cancel = tk.Button(self.toplevel, bd=5, text='    CANCEL    ', command=self.kill)
        self.but_cancel.grid(column=2, row=4)

        # AOB
        self.toplevel.grab_set()
        self.toplevel.iconbitmap(FAVICO)
        self.toplevel.resizable(0,0)
        root_x, root_y, dx, dy, w, h = window_positioning(self.toplevel)
        self.toplevel.geometry('{}x{}+{}+{}'.format(w, h, root_x + dx, root_y + dy))
        self.toplevel.update()
        self.toplevel.deiconify()
        root.wait_window(self.toplevel)

    def play_preview(self):
        self.toplevel.iconify()
        self.but_preview.config(state='disabled')
        w = popup_wait('Please wait while audio preview is being mixed...')
        # do the preview
        ratio = int(self.e_mix.get().strip())
        preview = trio.upload_wave(self.wav_file_name, self.full_file_name, self.part_num, ratio, self.gain_var.get(), SCRIPT_DIR, w)
        w.kill()

        w = popup_wait('Playing 10 seconds audio preview NOW', PICS['IMG_PREVIEW'], 'PLAYING AUDIO NOW')
        trio.preview_mix(*preview, 10) # List unpacking
        w.kill()
        self.but_preview.config(state='normal')
        self.toplevel.deiconify()
        self.toplevel.grab_set()
        self.toplevel.focus()


    def cb(self):
        # print("variable is", self.gain_var.get())
        pass

    def ok(self):
        self.toplevel.iconify()
        self.but_preview.config(state='disabled')
        w = popup_wait('Please wait while audio is being mixed and uploaded.\n\nOverdub parts will take 2 rounds of mixing.\n')
        # do the preview
        ratio = int(self.e_mix.get().strip())
        error, file_name = trio.upload_wave(self.wav_file_name, self.full_file_name, self.part_num, ratio, self.gain_var.get(), os.path.dirname(os.path.abspath(__file__)), w, False)
        w.kill()
        if error:
            if error.startswith('WARNING'):
                popup_ok(error, PICS['IMG_ERR_UPLOAD'])
            else: # abort!
                popup_ok(error, PICS['IMG_ERR_UPLOAD'])
                return
        message = 'Audio has been uploaded. The resulting .tlsd file has been written:\n'+file_name
        message += '\n\nThis file will now be selected and loaded\nso that you can upload audio to other parts.'
        popup_ok(message, PICS['IMG_OK'], 'ALL GOOD')
        click_folder_open(file_name)
        self.kill()
    
    def validate(self, e_mix_text):
        """
        ensures that e_mix_text is:
        integer
        always 3 char max.
        = 20, if empty
        >= 0 ... <= 100
        """
        if len(e_mix_text.get()) > 0:
            self.e_mix_text.set(self.e_mix_text.get()[:3])
            new_value=''
            old_value = self.e_mix_text.get()
            for char in old_value:
                try:
                    _ = int(char)
                except:
                    _ = None
                if isinstance(_, int):
                    new_value += str(_)
            if new_value:    
                new_value = int(new_value)
                if new_value < 0:
                    new_value = 0
                if new_value > 100:
                    new_value = 100
            else:
                new_value = 20

            self.e_mix_text.set(new_value)
    
    def generate():
        return self.toplevel
    
    def kill(self):
        self.toplevel.destroy()   

def click_export():
    continue_ = False
    for button in part_button.all_buttons_source:
         if button.part_state in ['recorded', 'overdub']:
             continue_ = True
             break
    if not continue_:
        message = '\n\nIn order to export .wav, your .tlsd file must contain\nat least one recorded or overdub part\n\n'
        popup_ok(message, PICS['IMG_ERR_EXPORT'])
        return
    
    w = popup_wait('Please wait while your .wav files are being extracted')
    index = int(lb.curselection()[0])
    file_name = Full_Filenames[index]
    data = trio.readBytes(file_name)
    parts = trio.getPartInfo(data)
    parts_with_audio = trio.give_parts_with_audio_only(parts)
    audioBlocks = trio.formAudioParts(parts_with_audio, data)
    errors = trio.write_wave_files(ntpath.basename(file_name), audioBlocks)
    w.kill()

    if errors:
        message = 'During .wav export, we encountered the following error(s):\n\n'
        message += '\n'.join(errors)
        popup_ok(message, PICS['IMG_ERR_EXPORT'])
    else:
        message = 'Your .wav files have been successfully extracted here:\n\n'+str(ntpath.abspath(trio.wavDir))
        popup_ok(message, PICS['IMG_OK'], 'ALL GOOD')

def click_save(evt=None):
    # check if filename is acceptable
    err_codes = {'min1': 'Please input at least one alpabetical letter',
                'alnum': 'Please input only alphanumerical letters and spaces',
                'minmax': 'Please input at least 1 and up to 16 characters',
                'found_file': 'File already exists. Please choose another filename'}
    global New_File_Name
    New_File_Name = e_fname.get().rstrip()
    
    err_str = trio.check_filename_for_new_file(New_File_Name, os.path.dirname(os.path.abspath(__file__)))
    if err_str:
        message = '\n\nFilename: '+New_File_Name+'.tlsd\n\nError:\n'+err_codes[err_str]+'\n\n'
        popup_ok(message, PICS['IMG_ERR_FILE'])
        return

    # at least one part trained?
    continue_ = False
    for button in part_button.all_buttons_target:
         if button.part_state in ['trained', 'recorded', 'overdub']:
            continue_ = True
            break
    if not continue_:
        message = '\n\nYour new .tlsd file must contain\nat least one trained, recorded\nor overdub part\n\n'
        popup_ok(message, PICS['IMG_ERR_EXPORT'])
        return
    
    # try reading empty template data
    empty_template = trio.read_empty_template(SCRIPT_DIR)
    if not empty_template:
        message='Expected file:\n'+str(trio.rsc_empty_song)+'\n...but could not load it.\n\nPlease get the latest release of this script from GitHub, extract all files and try again!'
        popup_ok(message, PICS['IMG_CANCEL_BIG'])
        return

    # start building new file
    w = popup_wait('Please wait while your .tlsd file is being created')
    all_info = part_button.new_file_info()
    containers, errors = trio.prepare_containers(all_info)
    if errors:
        w.kill()
        message = '\n'.join(errors)+'\n\nAbort new file creation!'
        popup_ok(message, PICS['IMG_CANCEL_BIG'])
        return
    
    error = trio.build_new_file(ntpath.abspath(New_File_Name+'.tlsd'), containers, empty_template)
    if error:
        w.kill()
        message = 'Unable to write file:\n'+error+'\n\nAbort new file creation!'
        popup_ok(message, PICS['IMG_CANCEL_BIG'])
        return
    
    w.kill()
    message = 'Your new .tlsd file has been successfully created here:\n\n'+ntpath.abspath(New_File_Name+'.tlsd')
    popup_ok(message, PICS['IMG_OK'], 'ALL GOOD')
    click_cancel_new_file()
    click_folder_open(ntpath.abspath(New_File_Name+'.tlsd'))

def click_upload():
    # initial checks
    continue_ = False
    for item in part_button.all_buttons_source:
        if item.clicked == True:
            continue_ = True
            state = item.part_state
            part_num = item.button_number
            full_file_name = item.full_filename
            break
    if not continue_:
        selected_target = False
        for item in part_button.all_buttons_target:
            if item.clicked == True:
                selected_target = True
                break
        if selected_target:
            message = '\n\nYou have selected a target part but for .wav upload\nyou need to select a SOURCE part.\n\n'
        else:
            message = '\n\nIn order to uplopad .wav, select a SOURCE part first.\n\n'
        popup_ok(message, PICS['IMG_ERR_UPLOAD'])
        return
    if state == 'empty' or state == 'none':
        message = '\n\nCannot upload .wav to an empty part!\n\nSelected source part must be \'trained\', \'recorded\' or \'overdub\'.\n\n'
        popup_ok(message, PICS['IMG_ERR_UPLOAD'])
        return

    # actual work...
    opts = {}
    opts['filetypes'] = [('RIFF WAV 16 bit Mono @ 44.1 kHz', ('.wav'))]
    wav_file_name = filedialog.askopenfilename(parent=root, initialdir=lbl_display_path.cget(
            'text'), title='Select a *.wav file for upload', **opts)
    if not wav_file_name:
        return
    upload(wav_file_name, part_num, full_file_name)

def click_beer():
    toplevel = tk.Toplevel()
    toplevel.grab_set()
    toplevel.resizable(0, 0)
    toplevel.iconbitmap(FAVICO)
    lbl_peter = tk.Label(toplevel, image=PICS['IMG_PETER'])
    lbl_peter.image = PICS['IMG_PETER']
    lbl_peter.pack()
    root_x, root_y, dx, dy, w, h = window_positioning(toplevel)
    toplevel.geometry('{}x{}+{}+{}'.format(w, h, root_x + dx, root_y + dy))

def click_cancel_new_file():
    render_buttons('target')
    for i in range(5):
        durations_target[i].config(text='0 s')
    lbl_target_log.config(text='Create your new *tlsd file here:\n\
01 - select any of the 5 part icons in the TARGET area\n\
02 - select any of the 5 part icons in the SOURCE area (*)\n\
03 - repeat until finished; \'?\'-parts will be treated as \'empty\' upon saving\n\
\n* note: you can selcet source-parts of different *.tlsd files!')

def click_quit(evt=None):  # * * *  C H A N G E  M E * * *
    if messagebox.askyesno("Quit?", "Really leave?", default='yes'):
        root.destroy()

def render_buttons(destination='source', file_name=''):
    """
    read file, if given, and extract part info
    create part_button instances accordingly
    place buttons on grid
    update global part_buttons instances list for source and target
    update duration labels source
    """
    if destination == 'source':
        part_button.all_buttons_source = []
    else:
        part_button.all_buttons_target = []

    buttons = []

    if file_name:
        data = trio.readBytes(file_name)
        parts = trio.getPartInfo(data)

        for part_num, part in enumerate(parts):
            duration = part.time_lenght
            if part.get_trained():
                if part.has_audio():
                    if part.has_overdub():
                        buttons.append(part_button(part_num, destination, 'overdub', duration, file_name))
                    else:
                        buttons.append(part_button(part_num, destination, 'recorded', duration, file_name))
                else:
                    buttons.append(part_button(part_num, destination, 'trained', duration, file_name))
            else:
                buttons.append(part_button(part_num, destination, 'empty', duration, file_name))
    else:
        for i in range(5):
            buttons.append(part_button(i, destination, 'none'))

    # render job; update global list
    for column, button in enumerate(buttons):
        button.button.grid(column=column, row=1)
        if destination == 'source':
            part_button.all_buttons_source.append(button)
        else:
            part_button.all_buttons_target.append(button)
    
    # update source durations
    for i, lbl in enumerate(durations_source):
        lbl.config(text=str(part_button.all_buttons_source[i].duration)+' s')

def click_folder_open(file_name=''):
    dir_name = ''
    opts = {}
    opts['filetypes'] = [('Trio+ Data File', ('.tlsd')), ]
    if not file_name:
        file_name = filedialog.askopenfilename(parent=root, initialdir=lbl_display_path.cget(
            'text'), title='Select a *.tlsd file', **opts)
    if file_name:
        dir_name = os.path.dirname(file_name)
        lbl_current_file.config(
            text='Selected (\'source area\'): ' + ntpath.basename(file_name))

    if dir_name:
        fill_lb(dir_name, file_name)
        if len(dir_name) > 70:
            dir_name='...'+dir_name[-67:]
        lbl_display_path.config(text=dir_name)

def click_refresh():
    dir_name = lbl_display_path.cget('text')
    fill_lb(dir_name)


# - - - BUTTONS - - -
border = 5

# Open Path
but_open_folder = tk.Button(
    frm_files_icons, image=PICS['IMG_OPEN'], bd=border, command=click_folder_open)
but_open_folder.image = PICS['IMG_OPEN']
but_open_folder.grid(column=0, row=1)

# Refresh
but_refresh = tk.Button(
    frm_files_icons, image=PICS['IMG_REFRESH'], bd=border, command=click_refresh)
but_refresh.image = PICS['IMG_REFRESH']
but_refresh.grid(column=1, row=1)

# save new file
but_save = tk.Button(frm_cancel_save, bd=border, image=PICS['IMG_SAVE'], command=lambda:click_save(None))
but_save.image = PICS['IMG_SAVE']
but_save.grid(column=0, row=3)

# cancel new file
but_cancel_new_file = tk.Button(frm_cancel_save, bd=border, image=PICS['IMG_CANCEL'], command=click_cancel_new_file)
but_cancel_new_file.image = PICS['IMG_CANCEL']
but_cancel_new_file.grid(column=0, row=1)

# export wav
but_export_wav = tk.Button(frm_exp_upload, bd=border, image=PICS['IMG_EXPORT'], command=click_export)
but_export_wav.image=PICS['IMG_EXPORT']
but_export_wav.grid(column=0, row=1)

# upload wav
but_upload_wav = tk.Button(frm_exp_upload, bd=border, image=PICS['IMG_UPLOAD'], command=click_upload)
but_upload_wav.image=PICS['IMG_UPLOAD']
but_upload_wav.grid(column=0, row=3)

# beer!
but_beer = tk.Button(frm_beer, image=PICS['IMG_BEER'], command=click_beer)
but_beer.image=PICS['IMG_BEER']
but_beer.grid(column=1, row=0, sticky='E')

# - - - LISTBOX - - -
def fill_lb(dir_name, selected_filename_from_dialog=''):
    global Full_Filenames
    Full_Filenames = []
    lb.delete(0, 'end')
    file_list = glob(dir_name + '/*' + EXT)
    for file_name in file_list:
        Full_Filenames.append(file_name)
        file_name = ntpath.basename(file_name)
        lb.insert('end', file_name)

    if file_list:
        if selected_filename_from_dialog:
            index = lb.get(0, "end").index(ntpath.basename(selected_filename_from_dialog))
        else:
            index = 0
        lb.select_set(index)
        lb.activate(index)
        lb.event_generate("<<ListboxSelect>>")
    else:
        # render_buttons_source('')
        render_buttons()

def lb_onselect(evt):
    # Note here that Tkinter passes an event object to onselect()
    w = evt.widget
    if w:
        index = int(w.curselection()[0])
        value = Full_Filenames[index]
        lbl_current_file.config(
            text='Selected (\'source area\'): ' + ntpath.basename(value))
        # render_buttons_source(value)
        render_buttons('source', value)


lb = tk.Listbox(frm_files, height=28, width=50,
                selectforeground='#e6e6fa', selectbackground='#0000ff', font=CUSTOM_FONT)
lb.bind('<<ListboxSelect>>', lb_onselect)
lb.grid(column=0, columnspan=2, row=2)

# - - - LABEL - - -
lbl_path_to_tlsd = tk.Label(
    frm_files, text='Select your *.tlsd files:', font=CUSTOM_FONT)
lbl_path_to_tlsd.grid(column=0, row=0, sticky='W')

lbl_display_path = tk.Label(frm_files, text=os.path.dirname(os.path.abspath(__file__)), font=CUSTOM_FONT_SMALL)
lbl_display_path.grid(column=0, columnspan=2, row=1, sticky='W')

lbl_status = tk.Label(frm_status, text='', anchor='center', justify='center', font=CUSTOM_FONT_SMALL)
lbl_status.config(text='The Trio+ GUI Tool (v0.80)\t\tby giveabit@mail.ru\t\tPublished on GitHub: https://github.com/giveabit/Trio-Plus-Data\t\tCheers!')
lbl_status.grid(column=0, row=0)

lbl_current_file = tk.Label(frm_source, text='SELECTED FILE (\'source area\'): none', font=CUSTOM_FONT)
lbl_current_file.grid(column=0, columnspan=5, row=0, sticky='WE')

lbl_target_file = tk.Label(frm_target, text='create a NEW FILE below (\'target area\'):', font=CUSTOM_FONT)
lbl_target_file.grid(column=0, columnspan=5, row=0, sticky='WE')

lbl_enter_filename = tk.Label(frm_enter_filename, text='New filename: ', font=CUSTOM_FONT)
lbl_enter_filename.grid(column=0, row=0, sticky='W')

lbl_tlsd = tk.Label(frm_enter_filename, text='.tlsd\t\t', font=CUSTOM_FONT)
lbl_tlsd.grid(column=4, row=0, sticky='E')

lbl_cancel_new = tk.Label(frm_cancel_save, text='Reset Parts', font = CUSTOM_FONT_SMALL)
lbl_cancel_new.grid(column=0, row=0)

lbl_save = tk.Label(frm_cancel_save, text='\nSave new .tlsd file', font = CUSTOM_FONT_SMALL)
lbl_save.grid(column=0, row=2)

lbl_export = tk.Label(frm_exp_upload, text='Extract all .wavs from file', font = CUSTOM_FONT_SMALL)
lbl_export.grid(column=0, row=0)

lbl_upload = tk.Label(frm_exp_upload, text='\nUpload .wav to selected part', font = CUSTOM_FONT_SMALL)
lbl_upload.grid(column=0, row=2)

lbl_open_path = tk.Label(frm_files_icons, text='Open file', font = CUSTOM_FONT_SMALL)
lbl_open_path.grid(column=0, row=0)

lbl_refresh = tk.Label(frm_files_icons, text='Update List', font = CUSTOM_FONT_SMALL)
lbl_refresh.grid(column=1, row=0)

durations_source = []
for i in range(5):
    durations_source.append(tk.Label(frm_source, text='0 s'))
    durations_source[i].grid(column=i, row=2, sticky='N')

durations_target = []
for i in range(5):
    durations_target.append(tk.Label(frm_target, text='0 s'))
    durations_target[i].grid(column=i, row=2, sticky='N')

lbl_target_log = tk.Label(frm_target, text='Create your new *tlsd file here:\n\
01 - select any of the 5 part icons in the TARGET area\n\
02 - select any of the 5 part icons in the SOURCE area (*)\n\
03 - repeat until finished; \'?\'-parts will be treated as \'empty\' upon saving\n\
\n* note: you can selcet source-parts of different *.tlsd files!',
            anchor='w', justify='left', font=CUSTOM_FONT_SMALL, width=65)
lbl_target_log.grid(column=0, columnspan=5, row=4, sticky='W')

# - - - ENTRY - - -
e_text = tk.StringVar()
e_fname = tk.Entry(frm_enter_filename, width=20, bg='#FFFFFF', font=CUSTOM_FONT, textvariable=e_text)
e_fname.insert(0, 'my new file')
e_fname.grid(column=1, row=0, sticky='WE')
e_fname.focus_set()
def fname_onselect(evt):
    if e_fname.get().strip() == 'my new file':
        e_fname.delete(0, 'end')
e_fname.bind('<Button-1>', fname_onselect)
def character_limit(e_text):
    if len(e_text.get()) > 0:
        e_text.set(e_text.get()[:16])
e_text.trace('w', lambda *args: character_limit(e_text))


# - - - LOGIC - - -
def window_positioning(widget):
    widget.update()
    root_x = root.winfo_x()
    root_y = root.winfo_y()
    dx = int(x_size/3)
    dy = int(y_size/3)
    w = widget.winfo_reqwidth()
    h = widget.winfo_reqheight()
    return root_x, root_y, dx, dy, w, h

# - - - INIT - - -
fill_lb(os.path.dirname(os.path.abspath(__file__)))  # will also render buttons_source
render_buttons('target')
# - - - MAIN - - -
root.protocol('WM_DELETE_WINDOW', click_quit)
#root.bind('<Return>', click_save)
root.bind('<Escape>', click_quit)
root.mainloop()
