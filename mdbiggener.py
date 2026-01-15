#!/usr/bin/env python3

"""Image interpolation algorithms test shell; rescaler; function-based variant.

Input: PNG, PPM, PGM, PBM.

Output: PNG, PPM, PGM.

----
Main site: `The Toad's Slimy Mudhole`_

.. _The Toad's Slimy Mudhole: https://dnyarri.github.io

Git repositories: `@Github`_, `@Gitflic`_.

.. _@Github: https://github.com/Dnyarri/imin

.. _@Gitflic: https://gitflic.ru/project/dnyarri/imin

"""

__author__ = 'Ilya Razmanov'
__copyright__ = '(c) 2025-2026 Ilya Razmanov'
__credits__ = 'Ilya Razmanov'
__license__ = 'unlicense'
__version__ = '26.1.15.7'
__maintainer__ = 'Ilya Razmanov'
__email__ = 'ilyarazmanov@gmail.com'
__status__ = 'Development'

from copy import deepcopy
from pathlib import Path
from random import randbytes  # Used for random icon only
from time import ctime, time
from tkinter import BooleanVar, Button, Checkbutton, Entry, Frame, IntVar, Label, Menu, Menubutton, OptionMenu, PhotoImage, StringVar, Tk
from tkinter.filedialog import askopenfilename, asksaveasfilename
from tkinter.messagebox import showinfo

from pypng.pnglpng import list2png, png2list
from pypnm.pnmlpnm import list2bin, list2pnm, pnm2list
from scalers import barycentric, bilinear

""" ╔══════════════════════════════════╗
    ║ GUI events and functions thereof ║
    ╚══════════════════════════════════╝ """


def DisMiss(event=None) -> None:
    """Kill dialog and continue."""

    sortir.destroy()


def ShowMenu(event) -> None:
    """Pop menu up (or sort of drop it down)."""

    menu02.post(event.x_root, event.y_root)


def ShowInfo(event=None) -> None:
    """Show image information."""

    file_size = Path(sourcefilename).stat().st_size
    file_size_str = f'{file_size / 1048576:.2f} Mb' if (file_size > 1048576) else f'{file_size / 1024:.2f} Kb' if (file_size > 1024) else f'{file_size} bytes'
    showinfo(
        title='Source image information',
        message=f'File properties:\nLocation: {sourcefilename}\nSize: {file_size_str}\nLast modified: {ctime(Path(sourcefilename).stat().st_mtime)}',
        detail=f'Image properties, as represented internally:\nStatus: {is_filtered=}, {is_saved=}\nWidth: {X} px\nHeight: {Y} px\nChannels: {Z} channel{"s" if Z > 1 else ""}\nColor depth: {maxcolors + 1} gradations/channel',
    )


def UINormal() -> None:
    """Normal UI state, buttons enabled."""

    for widget in frame_top.winfo_children():
        if widget.winfo_class() in ('Label', 'Button', 'OptionMenu', 'Checkbutton', 'Entry'):
            widget['state'] = 'normal'
        if widget.winfo_class() == 'Button':
            widget['cursor'] = 'hand2'
    method_menu['state'] = 'normal'
    info_string.config(text=info_normal['txt'], foreground=info_normal['fg'], background=info_normal['bg'])
    sortir.update()


def UIBusy() -> None:
    """Busy UI state, buttons disabled."""

    for widget in frame_top.winfo_children():
        if widget.winfo_class() in ('Label', 'Button', 'OptionMenu', 'Checkbutton', 'Entry'):
            widget['state'] = 'disabled'
        if widget.winfo_class() == 'Button':
            widget['cursor'] = 'arrow'
    method_menu['state'] = 'disabled'
    info_string.config(text=info_busy['txt'], foreground=info_busy['fg'], background=info_busy['bg'])
    sortir.update()


def ShowPreview(preview_name: PhotoImage, caption: str) -> None:
    """Show preview_name PhotoImage with caption below."""

    global zoom_factor, preview

    preview = preview_name

    if zoom_factor > 0:
        preview = preview.zoom(zoom_factor + 1)
        label_zoom['text'] = f'Zoom {zoom_factor + 1}:1'
    elif zoom_factor < 0:
        preview = preview.subsample(1 - zoom_factor)
        label_zoom['text'] = f'Zoom 1:{1 - zoom_factor}'
    else:
        preview = preview_name
        label_zoom['text'] = 'Zoom 1:1'

    zanyato.config(text=caption, font=('helvetica', 8), image=preview, compound='top', padx=0, pady=0, justify='center', background=zanyato.master['background'], relief='flat', borderwidth=1, state='normal')
    zanyato.pack_configure(pady=max(0, 16 - (preview.height() // 2)))


def syncXY():
    """Tries to make Y setting follow X change if square is on."""

    global XNEW, YNEW
    if ini_square.get():
        XNEW = max(2, ini_x.get())
        ini_x.set(XNEW)
        old = ini_y.get()
        new = max(2, round(Y * XNEW / X))
        if abs(new - old) > 1:
            ini_y.set(new)


def syncYX():
    """Tries to make X setting follow Y change if square is on."""

    global XNEW, YNEW
    if ini_square.get():
        YNEW = max(2, ini_y.get())
        ini_y.set(YNEW)
        old = ini_x.get()
        new = max(2, round(X * YNEW / Y))
        if abs(new - old) > 1:
            ini_x.set(new)


def GetSource(event=None) -> None:
    """Open source image and redefine other controls state."""

    global zoom_factor, view_src, is_filtered, is_saved, info_normal, color_mode_str
    global preview, preview_src, preview_filtered  # preview and copies of preview
    global X, Y, Z, XNEW, YNEW, maxcolors, image3D, info, sourcefilename
    global source_image3D  # deep copy of source data, to be used as a source for filtering

    zoom_factor = 0
    view_src = True
    is_filtered = False
    is_saved = True

    sourcefilename = askopenfilename(title='Open image file', filetypes=[('Supported formats', '.png .ppm .pgm .pbm .pnm'), ('Portable network graphics', '.png'), ('Portable any map', '.ppm .pgm .pbm .pnm')])
    if sourcefilename == '':
        return

    UIBusy()

    """ ┌────────────────────────────────────────┐
        │ Loading file, converting data to list. │
        │ NOTE: maxcolors, image3D, info MUST be │
        │ GLOBALS! They are used during saving!  │
        └────────────────────────────────────────┘ """

    if Path(sourcefilename).suffix.lower() == '.png':
        # ↓ Reading PNG image as list
        X, Y, Z, maxcolors, source_image3D, info = png2list(sourcefilename)

    elif Path(sourcefilename).suffix.lower() in ('.ppm', '.pgm', '.pbm', '.pnm'):
        # ↓ Reading PNM image as list
        X, Y, Z, maxcolors, source_image3D = pnm2list(sourcefilename)
        # ↓ Creating dummy info required to correctly Save As PNG later.
        #   Fixing color mode, the rest is fixed with pnglpng v. 25.01.07.
        info = {'bitdepth': 16} if maxcolors > 255 else {'bitdepth': 8}

    else:
        raise ValueError('Extension not recognized')

    """ ┌──────────┐
        │ New size │
        └──────────┘ """
    XNEW = X
    YNEW = Y
    ini_x.set(XNEW)
    ini_y.set(YNEW)

    """ ┌────────────────────────────────────────────┐
        │ Creating deep copy of source 3D list       │
        │ to avoid accumulating repetitive filtering │
        └────────────────────────────────────────────┘ """
    image3D = deepcopy(source_image3D)

    """ ┌───────────────┐
        │ Viewing image │
        └───────────────┘ """
    # ↓ Converting list to bytes of PNM-like structure "preview_data" in memory
    preview_data = list2bin(image3D, maxcolors, show_chessboard=True)
    # ↓ Now generating preview from "preview_data" bytes using Tkinter
    preview = PhotoImage(data=preview_data)
    # ↓ Finally the show part
    ShowPreview(preview, 'Source')

    """ ┌─────────────────────────────────────────────┐
        │ Creating copy of source preview for further │
        │ switch between source and result            │
        └─────────────────────────────────────────────┘ """
    preview_src = preview_filtered = preview

    # ↓ Attempt to zoom to fit. Singe zoomOut() must fit for a reasonable image size.
    #   GUI X extra = 8 px, GUI Y extra = 150 px
    if X + 16 > sortir.winfo_screenwidth() or Y + 152 > sortir.winfo_screenheight():
        zoomOut()

    # ↓ binding on preview click
    zanyato.bind('<Control-Button-1>', zoomIn)  # Ctrl + left click
    zanyato.bind('<Double-Control-Button-1>', zoomIn)  # Ctrl + left click too fast
    zanyato.bind('<Control-+>', zoomIn)
    zanyato.bind('<Control-=>', zoomIn)
    zanyato.bind('<Alt-Button-1>', zoomOut)  # Alt + left click
    zanyato.bind('<Double-Alt-Button-1>', zoomOut)  # Alt + left click too fast
    zanyato.bind('<Control-minus>', zoomOut)
    zanyato.bind('<Control-Key-1>', zoomOne)
    zanyato.bind('<Control-Alt-Key-0>', zoomOne)
    sortir.bind_all('<MouseWheel>', zoomWheel)  # Wheel scroll
    sortir.bind_all('<Control-i>', ShowInfo)
    menu02.entryconfig('Image Info...', state='normal')
    # ↓ Spin
    in01.unbind('<MouseWheel>')
    in01.bind('<MouseWheel>', incWheel)
    in02.unbind('<MouseWheel>')
    in02.bind('<MouseWheel>', incWheel)
    # ↓ binding global
    sortir.bind_all('<Return>', RunFilter)
    # ↓ enabling save
    menu02.entryconfig('Save as...', state='normal')
    sortir.bind_all('<Control-Shift-S>', SaveAs)
    # ↓ enabling zoom buttons
    butt_plus.config(state='normal', cursor='hand2')
    butt_minus.config(state='normal', cursor='hand2')
    # ↓ Adding filename, mode and status to window title a-la Photoshop
    if Z == 1:
        color_mode_str = f' (L:{"8" if maxcolors < 256 else "16"})'
    elif Z == 2:
        color_mode_str = f' (LA:{"8" if maxcolors < 256 else "16"})'
    elif Z == 3:
        color_mode_str = f' (RGB:{"8" if maxcolors < 256 else "16"})'
    elif Z == 4:
        color_mode_str = f' (RGBA:{"8" if maxcolors < 256 else "16"})'
    else:
        color_mode_str = ''  # Just in case
    sortir.title(f'{product_name}: {Path(sourcefilename).name}{color_mode_str}{"*" if is_filtered else ""}')
    info_normal = {'txt': f'{Path(sourcefilename).name}{"*" if is_filtered else ""} X={X} Y={Y} Z={Z} maxcolors={maxcolors}', 'fg': 'grey', 'bg': 'grey90'}
    # ↓ enabling "Filter"
    butt_filter.bind('<Enter>', lambda event=None: butt_filter.config(foreground=butt['activeforeground'], background=butt['activebackground']))
    butt_filter.bind('<Leave>', lambda event=None: butt_filter.config(foreground=butt['foreground'], background=butt['background']))
    UINormal()
    sortir.geometry(f'+{(sortir.winfo_screenwidth() - sortir.winfo_width()) // 2}+{(sortir.winfo_screenheight() - sortir.winfo_height()) // 2 - 32}')
    zanyato.focus_set()


def RunFilter(event=None) -> None:
    """Filter image, then preview result."""

    global zoom_factor, view_src, is_filtered, is_saved, info_normal, color_mode_str, timing
    global preview, preview_filtered
    global X, Y, Z, maxcolors, image3D, source_image3D, info

    # ↓ filtering parameters
    method = method_str.get()
    XNEW = ini_x.get()
    YNEW = ini_y.get()
    ini_x.set(XNEW)
    ini_y.set(YNEW)

    UIBusy()

    """ ┌─────────────────┐
        │ Filtering image │
        └─────────────────┘ """
    if method == 'Bilinear':
        start = time()
        image3D = bilinear.scale(source_image3D, XNEW, YNEW, edge=1)
        timing = time() - start
    elif method == 'Barycentric':
        start = time()
        image3D = barycentric.scale(source_image3D, XNEW, YNEW, edge=1)
        timing = time() - start

    Y = len(source_image3D)
    X = len(source_image3D[0])
    Z = len(source_image3D[0][0])

    # ↓ preview result
    preview_data = list2bin(image3D, maxcolors, show_chessboard=True)
    preview_filtered = PhotoImage(data=preview_data)
    ShowPreview(preview_filtered, 'Result')

    # ↓ Flagging as filtered, not saved
    is_filtered = True
    is_saved = False
    view_src = False

    # ↓ enabling save
    menu02.entryconfig('Save', state='normal')
    # ↓ binding global
    sortir.bind_all('<Control-s>', Save)
    # ↓ binding switch on preview click
    zanyato.bind('<Button-1>', SwitchView)  # left click
    zanyato.bind('<space>', SwitchView)  # # "Space" key. May be worth binding whole sortir?
    # ↓ Adding filename, mode and status to window title a-la Photoshop
    sortir.title(f'{product_name}: {Path(sourcefilename).name}{color_mode_str}{"*" if is_filtered else ""}')
    info_normal = {'txt': f'{Path(sourcefilename).name}{"*" if is_filtered else ""} X={XNEW if is_filtered else X} Y={YNEW if is_filtered else Y} Z={Z} maxcolors={maxcolors}', 'fg': 'grey', 'bg': 'grey90'}
    UINormal()
    zanyato.focus_set()  # moving focus to preview


def zoomIn(event=None) -> None:
    """Zoom preview in."""

    global zoom_factor, view_src, preview
    zoom_factor = min(zoom_factor + 1, 4)  # max zoom 5

    if view_src:
        ShowPreview(preview_src, 'Source')
    else:
        ShowPreview(preview_filtered, 'Result')

    # ↓ reenabling +/- buttons
    butt_minus.config(state='normal', cursor='hand2')
    if zoom_factor == 4:  # max zoom 5
        butt_plus.config(state='disabled', cursor='arrow')
    else:
        butt_plus.config(state='normal', cursor='hand2')


def zoomOut(event=None) -> None:
    """Zoom preview out."""

    global zoom_factor, view_src, preview
    zoom_factor = max(zoom_factor - 1, -4)  # min zoom 1/5

    if view_src:
        ShowPreview(preview_src, 'Source')
    else:
        ShowPreview(preview_filtered, 'Result')

    # ↓ reenabling +/- buttons
    butt_plus.config(state='normal', cursor='hand2')
    if zoom_factor == -4:  # min zoom 1/5
        butt_minus.config(state='disabled', cursor='arrow')
    else:
        butt_minus.config(state='normal', cursor='hand2')


def zoomOne(event=None) -> None:
    """Zoom 1:1."""

    global zoom_factor, view_src, preview
    zoom_factor = 0

    if view_src:
        ShowPreview(preview_src, 'Source')
    else:
        ShowPreview(preview_filtered, 'Result')

    # ↓ reenabling +/- buttons
    butt_plus.config(state='normal', cursor='hand2')
    butt_minus.config(state='normal', cursor='hand2')


def zoomWheel(event) -> None:
    """zoomIn or zoomOut by mouse wheel."""

    if event.widget not in transparent_controls:
        if event.delta < 0:
            zoomOut()
        if event.delta > 0:
            zoomIn()


def SwitchView(event=None) -> None:
    """Switch preview between preview_src and preview_filtered."""

    global zoom_factor, view_src, preview
    view_src = not view_src
    if view_src:
        ShowPreview(preview_src, 'Source')
    else:
        ShowPreview(preview_filtered, 'Result')


def onSave() -> None:
    global sourcefilename, resultfilename, is_saved
    global source_image3D, image3D, X, Y, Z, maxcolors
    global preview_data, preview_filtered, preview_src, info_normal

    sourcefilename = resultfilename  # Now saved file becomes new source file
    source_image3D = deepcopy(image3D)
    preview_data = list2bin(image3D, maxcolors, show_chessboard=True)
    preview_filtered = PhotoImage(data=preview_data)
    preview_src = preview_filtered

    # ↓ disabling save
    menu02.entryconfig('Save', state='disabled')
    sortir.unbind_all('<Control-s>')
    # ↓ binding switch on preview click
    zanyato.unbind('<Button-1>')  # left click
    zanyato.unbind('<space>')  # # "Space" key. May be worth binding whole sortir?
    # ↓ preview source
    ShowPreview(preview_src, 'Source')
    # ↓ Adding filename, mode and status to window title a-la Photoshop
    sortir.title(f'{product_name}: {Path(sourcefilename).name}{color_mode_str}{"*" if is_filtered else ""}')
    info_normal = {'txt': f'{Path(sourcefilename).name}{"*" if is_filtered else ""} X={X} Y={Y} Z={Z} maxcolors={maxcolors}', 'fg': 'grey', 'bg': 'grey90'}
    UINormal()


def Save(event=None) -> None:
    """Once pressed on Save."""

    global is_filtered, is_saved, info_normal, color_mode_str
    global source_image3D, sourcefilename, resultfilename

    if is_saved:  # block repetitive saving
        return
    if not is_filtered:  # block useless source resaving
        return
    resultfilename = sourcefilename
    UIBusy()
    # ↓ Save format choice
    if Path(resultfilename).suffix.lower() == '.png':
        info['compression'] = 9  # Explicitly setting compression
        list2png(resultfilename, image3D, info)  # Writing file
    elif Path(resultfilename).suffix.lower() in ('.ppm', '.pgm', '.pnm'):
        list2pnm(resultfilename, image3D, maxcolors)  # Writing file
    # ↓ Flagging image as saved, not filtered
    is_saved = True  # to block future repetitive saving
    is_filtered = False
    # ↓ Now saved file becomes new source file
    onSave()
    UINormal()


def SaveAs(event=None) -> None:
    """Once pressed on Save as..."""

    global is_saved, is_filtered, info_normal, color_mode_str
    global source_image3D, sourcefilename, resultfilename

    # ↓ Adjusting "Save as" formats to be displayed
    #   according to bitdepth and source extension
    src_extension = Path(sourcefilename).suffix.lower()
    if Z == 1:
        if src_extension in ('.pgm', '.pnm'):
            format_list = [('Portable grey map', '.pgm'), ('Portable network graphics', '.png')]
            proposed_name = Path(sourcefilename).stem + '.pgm'
        else:
            format_list = [('Portable network graphics', '.png'), ('Portable grey map', '.pgm')]
            proposed_name = Path(sourcefilename).stem + '.png'
    elif Z == 2:
        format_list = [('Portable network graphics', '.png')]
        proposed_name = Path(sourcefilename).stem + '.png'
    elif Z == 3:
        if src_extension in ('.ppm', '.pnm'):
            format_list = [('Portable pixel map', '.ppm'), ('Portable network graphics', '.png')]
            proposed_name = Path(sourcefilename).stem + '.ppm'
        else:
            format_list = [('Portable network graphics', '.png'), ('Portable pixel map', '.ppm')]
            proposed_name = Path(sourcefilename).stem + '.png'
    else:
        format_list = [('Portable network graphics', '.png')]
        proposed_name = Path(sourcefilename).stem + '.png'

    # ↓ Open export file
    resultfilename = asksaveasfilename(
        title='Save image file',
        filetypes=format_list,
        defaultextension='.png',  # No extension should never happen but just in case
        initialdir=Path(sourcefilename).parent,
        initialfile=proposed_name,
    )
    if resultfilename == '':
        return None
    UIBusy()
    # ↓ Save format choice
    if Path(resultfilename).suffix.lower() == '.png':
        info['compression'] = 9  # Explicitly setting compression
        list2png(resultfilename, image3D, info)  # Writing file
    elif Path(resultfilename).suffix.lower() in ('.ppm', '.pgm'):
        list2pnm(resultfilename, image3D, maxcolors)  # Writing file
    else:
        raise ValueError('Extension not recognized')
    # ↓ Flagging image as saved, not filtered, and disabling "Save"
    is_saved = True  # to block future repetitive saving
    is_filtered = False
    # ↓ Now saved file becomes new source file
    onSave()
    UINormal()


def valiDig(new_value):
    """Try to block non-integer input."""

    try:
        _ = int(new_value)
        if _ > 1 and _ < 2048:
            return True
        else:
            return False
    except ValueError:
        return False


def incWheel(event) -> None:
    """Increment or decrement entries by mouse wheel."""

    if event.widget == in01:
        if event.delta < 0:
            ini_x.set(min(2048, max(2, ini_x.get() - 1)))
        if event.delta > 0:
            ini_x.set(min(2048, max(2, ini_x.get() + 1)))
    if event.widget == in02:
        if event.delta < 0:
            ini_y.set(min(2048, max(2, ini_y.get() - 1)))
        if event.delta > 0:
            ini_y.set(min(2048, max(2, ini_y.get() + 1)))


""" ╔═══════════╗
    ║ Main body ║
    ╚═══════════╝ """

zoom_factor = 0
view_src = True
is_filtered = False
timing = None
product_name = '[Em|De]biggener'

sortir = Tk()

sortir.iconphoto(True, PhotoImage(data='P6\n8 8\n255\n'.encode(encoding='ascii') + randbytes(8 * 8 * 3)))
sortir.title(product_name)

validate_entry = sortir.register(valiDig)

# ↓ Info statuses dictionaries
info_normal = {'txt': f'{product_name} {__version__}', 'fg': 'grey', 'bg': 'grey90'}
info_busy = {'txt': 'BUSY, PLEASE WAIT', 'fg': 'red', 'bg': 'yellow'}
color_mode_str = ' '

# ↓ Buttons dictionaries
butt = {
    'font': ('helvetica', 12),
    'cursor': 'hand2',
    'border': '2',
    'relief': 'groove',
    'overrelief': 'raised',
    'foreground': 'SystemButtonText',
    'background': 'SystemButtonFace',
    'activeforeground': 'dark blue',
    'activebackground': '#E5F1FB',
}

# ↓ Info string
info_string = Label(sortir, text=info_normal['txt'], font=('courier', 7), foreground=info_normal['fg'], background=info_normal['bg'], relief='groove')
info_string.pack(side='bottom', padx=0, pady=(2, 0), fill='both')
# ↓ Info string binding for displaying scaler execution time
info_string.bind('<Enter>', lambda event=None: info_string.config(text=f'Run time: {timing}'))
info_string.bind('<Leave>', lambda event=None: UINormal())
info_string.bind('<Control-Button-1>', lambda event=None: [sortir.clipboard_clear(), sortir.clipboard_append(f'{timing}\n')])

# ↓ initial sortir binding, before image load
sortir.bind_all('<Button-3>', ShowMenu)  # Popup menu
sortir.bind_all('<Alt-f>', ShowMenu)
sortir.bind_all('<Control-o>', GetSource)
sortir.bind_all('<Control-q>', DisMiss)

frame_top = Frame(sortir, borderwidth=2, relief='groove')
frame_top.pack(side='top', anchor='w', pady=(0, 2))
frame_preview = Frame(sortir, borderwidth=2, relief='groove')
frame_preview.pack(side='top', anchor='center', expand=True)

""" ┌──────────────────────┐
    │ Top frame (controls) │
    └─────────────────────-┘ """

col = 0

# ↓ File menu
butt_file = Menubutton(
    frame_top,
    text='File...',
    width=8,
    anchor='w',
    font=butt['font'],
    cursor=butt['cursor'],
    relief=butt['relief'],
    activeforeground=butt['activeforeground'],
    activebackground=butt['activebackground'],
    border=butt['border'],
    state='normal',
    indicatoron=False,
)
butt_file.grid(row=0, column=col, rowspan=2, sticky='ns', padx=(0, 10), pady=0)
col += 1

menu02 = Menu(butt_file, tearoff=False)  # "File" menu
menu02.add_command(label='Open...', state='normal', command=GetSource, accelerator='Ctrl+O')
menu02.add_separator()
menu02.add_command(label='Save', state='disabled', command=Save, accelerator='Ctrl+S')
menu02.add_command(label='Save as...', state='disabled', command=SaveAs, accelerator='Ctrl+Shift+S')
menu02.add_separator()
menu02.add_command(label='Image Info...', accelerator='Ctrl+I', state='disabled', command=ShowInfo)
menu02.add_separator()
menu02.add_command(label='Exit', state='normal', command=DisMiss, accelerator='Ctrl+Q')

butt_file['menu'] = menu02

butt_file.bind('<Enter>', lambda event=None: butt_file.config(relief=butt['overrelief']))
butt_file.bind('<Leave>', lambda event=None: butt_file.config(relief=butt['relief']))

butt_file.focus_set()  # Setting focus to "File..."

# ↓ Filter section begins
info00 = Label(frame_top, text='Size:', font=('helvetica', 8, 'italic'), justify='right', foreground='brown', state='disabled')
info00.grid(row=0, column=col)
col += 1

# ↓ X-size control
info01 = Label(frame_top, text='X:', font=('helvetica', 11), state='disabled')
info01.grid(row=0, column=col)
col += 1

ini_x = IntVar(value=2)
in01 = Entry(frame_top, textvariable=ini_x, state='disabled', width=5, font=('helvetica', 11), validate='key', validatecommand=(validate_entry, '%P'))
in01.grid(row=0, column=col)
col += 1

# ↓ bind x and y effects
ini_square = BooleanVar(value=True)
check01 = Checkbutton(frame_top, variable=ini_square, onvalue=True, offvalue=False, indicatoron=0, text='✕', font=('courier', 8), state='disabled', relief=butt['relief'], borderwidth=1, command=syncXY)
check01.grid(row=0, column=col, padx=(4, 2))
col += 1

# ↓ Y-size control
info02 = Label(frame_top, text='Y:', font=('helvetica', 11), state='disabled')
info02.grid(row=0, column=col)
col += 1

ini_y = IntVar(value=2)
in02 = Entry(frame_top, textvariable=ini_y, state='disabled', width=5, font=('helvetica', 11), validate='key', validatecommand=(validate_entry, '%P'))
in02.grid(row=0, column=col)
col += 1

ini_x.trace_add('write', lambda *args: syncXY())
ini_y.trace_add('write', lambda *args: syncYX())

method_str = StringVar(value='Bilinear')
method_menu = OptionMenu(frame_top, method_str, *['Bilinear', 'Barycentric'])
method_menu.grid(row=0, column=col)
col += 1
method_menu.configure(indicatoron=True, font=('helvetica', 12), width=10, anchor='e', relief='groove', activebackground='#E5F1FB', state='disabled')
method_menu['menu'].configure(font=method_menu['font'])

# ↓ Filter start
butt_filter = Button(
    frame_top,
    text='Run',
    width=8,
    anchor='center',
    font=butt['font'],
    cursor='arrow',
    relief=butt['relief'],
    overrelief=butt['overrelief'],
    activeforeground=butt['activeforeground'],
    activebackground=butt['activebackground'],
    border=butt['border'],
    state='disabled',
    command=RunFilter,
)
butt_filter.grid(row=0, column=col, sticky='nsew', padx=(10, 0), pady=0)

""" ┌──────────────────────────────┐
    │ Center frame (image preview) │
    └─────────────────────────────-┘ """
zanyato = Label(
    frame_preview,
    text='Preview area.\n  Double click to open image,\n  Right click or Alt+F for a menu.\nWith image opened,\n  Ctrl+Click to zoom in,\n  Alt+Click to zoom out,\n  Enter to filter.\nWhen filtered, click or Space bar\nto switch source/result.',
    font=('helvetica', 12),
    justify='left',
    borderwidth=2,
    padx=24,
    pady=24,
    background='grey90',
    relief='groove',
)
zanyato.bind('<Double-Button-1>', GetSource)  # Double-click to "Open"
frame_preview.bind('<Double-Button-1>', GetSource)
zanyato.pack(side='top')

frame_zoom = Frame(frame_preview, borderwidth=2, relief='groove')
frame_zoom.pack(side='bottom')

butt_plus = Button(frame_zoom, text='+', font=('courier', 8), width=2, cursor='arrow', state='disabled', borderwidth=1, command=zoomIn)
butt_plus.pack(side='left', padx=0, pady=0, fill='both')

butt_minus = Button(frame_zoom, text='-', font=('courier', 8), width=2, cursor='arrow', state='disabled', borderwidth=1, command=zoomOut)
butt_minus.pack(side='right', padx=0, pady=0, fill='both')

label_zoom = Label(frame_zoom, text='Zoom 1:1', font=('courier', 8), state='disabled')
label_zoom.pack(side='left', anchor='n', padx=2, pady=0, fill='both')

transparent_controls = (in01, in02)  # To be cut off global events

# ↓ Center window horizontally, +100 vertically
sortir.update()
# print(sortir.winfo_width(), sortir.winfo_height())
sortir.minsize(frame_top.winfo_width(), 320)
sortir.maxsize(9 * sortir.winfo_screenwidth() // 10, 9 * sortir.winfo_screenheight() // 10)
sortir.geometry(f'+{(sortir.winfo_screenwidth() - sortir.winfo_width()) // 2}+100')

sortir.mainloop()
