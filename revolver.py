#!/usr/bin/env python3

"""Image interpolation algorithms test shell; rotator; function-based variant.

Input: PNG, PPM, PGM, PBM.

Output: PNG, PPM, PGM.

----
**Main site**: `The Toad's Slimy Mudhole`_

.. _The Toad's Slimy Mudhole: https://dnyarri.github.io/

**Project page**: `imin`_

.. _imin: https://dnyarri.github.io/imin.html

**imin** Git repositories: main `@Github`_ and mirror `@Gitflic`_.

.. _@Github: https://github.com/Dnyarri/imin

.. _@Gitflic: https://gitflic.ru/project/dnyarri/imin

"""

__author__ = 'Ilya Razmanov'
__copyright__ = '(c) 2025-2026 Ilya Razmanov'
__credits__ = 'Ilya Razmanov'
__license__ = 'unlicense'
__version__ = '26.8.26.24'
__maintainer__ = 'Ilya Razmanov'
__email__ = 'ilyarazmanov@gmail.com'
__status__ = 'Development'

from copy import deepcopy
from math import cos, radians, sin
from pathlib import Path
from random import randbytes  # Used for random icon only
from time import ctime, time
from tkinter import Button, Canvas, DoubleVar, Frame, Label, Menu, Menubutton, OptionMenu, PhotoImage, Spinbox, StringVar, Tk
from tkinter.filedialog import askopenfilename, asksaveasfilename
from tkinter.messagebox import showinfo

from imin.displace import displace
from pypng import list2png, png2list
from pypnm import list2bin, list2pnm, pnm2list

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
        title='Image information',
        message=f'File properties:\nLocation: {sourcefilename}\nSize: {file_size_str}\nLast modified: {ctime(Path(sourcefilename).stat().st_mtime)}',
        detail=f'Image properties, as represented internally:\nStatus: {is_filtered=}, {is_saved=}\nWidth: {X} px\nHeight: {Y} px\nChannels: {Z} channel{"s" if Z > 1 else ""}\nColor depth: {maxcolors + 1} gradations/channel',
    )


def UINormal() -> None:
    """Normal UI state, controls enabled."""

    for widget in frame_top.winfo_children():
        if widget.winfo_class() in ('Label', 'Button', 'Spinbox', 'OptionMenu', 'Checkbutton'):
            widget['state'] = 'normal'
        if widget.winfo_class() == 'Button':
            widget['cursor'] = 'hand2'
    method_menu['state'] = 'normal'
    edge_menu['state'] = 'normal'
    info_string.config(text=info_normal['txt'], foreground=info_normal['fg'], background=info_normal['bg'])
    sortir.update()


def UIBusy() -> None:
    """Busy UI state, controls disabled."""

    for widget in frame_top.winfo_children():
        if widget.winfo_class() in ('Label', 'Button', 'Spinbox', 'OptionMenu', 'Checkbutton'):
            widget['state'] = 'disabled'
        if widget.winfo_class() == 'Button':
            widget['cursor'] = 'arrow'
    method_menu['state'] = 'disabled'
    edge_menu['state'] = 'disabled'
    info_string.config(text=info_busy['txt'], foreground=info_busy['fg'], background=info_busy['bg'])
    sortir.update()


def UIFit() -> None:
    """Readopting 'sortir.minsize' to fit the screen."""

    sortir.update()
    fit_width = min(sortir.winfo_reqwidth(), 9 * sortir.winfo_screenwidth() // 10)
    fit_height = min(sortir.winfo_reqheight(), 9 * sortir.winfo_screenheight() // 10)
    sortir.minsize(fit_width, fit_height)


def canvasCoord(event):
    """Marking 'canvas' view point for further dragging."""

    canvas.scan_mark(event.x, event.y)


def canvasDrag(event):
    """Dragging 'canvas' Canvas."""

    canvas.scan_dragto(
        event.x,
        event.y,
        gain=1,
    )
    canvas['cursor'] = 'fleur'


def ShowPreview(preview_choice: PhotoImage, caption: str) -> None:
    """Show 'preview_choice' PhotoImage, trying to fit 'zanyato' to screen."""

    global preview

    preview = preview_choice

    if zoom_factor > 0:
        preview = preview.zoom(zoom_factor + 1)
        label_zoom['text'] = f'{caption} {zoom_factor + 1}:1'
    elif zoom_factor < 0:
        preview = preview.subsample(1 - zoom_factor)
        label_zoom['text'] = f'{caption} 1:{1 - zoom_factor}'
    else:
        label_zoom['text'] = f'{caption} 1:1'

    # ↓ Sizes of preview to fit the screen
    preview_width = min(preview.width(), 8 * sortir.winfo_screenwidth() // 10)
    preview_height = min(preview.height(), (8 * sortir.winfo_screenheight() // 10) - frame_top.winfo_height() - info_string.winfo_height() - frame_zoom.winfo_height())

    zanyato.config(
        image=preview,
        relief='flat',
        borderwidth=0,
    )
    canvas.config(
        width=preview_width,
        height=preview_height,  # Note that 'scrollregion' may be bigger than canvas!
        scrollregion=(0, 0, preview.width(), preview.height()),
        cursor='arrow',
    )
    canvas.itemconfig(  # configuring 'zanyato' size in a normal way doesn't work on canvas
        zanyato_,
        width=preview.width(),
        height=preview.height(),
    )


def SwitchView(event=None) -> None:
    """Switch preview between preview_src and preview_filtered."""

    global view_src
    global xs, xr, ys, yr  # view point coordinates in *s*ource and *r*esult image

    view_src = not view_src  # cycling before ⇄ after
    if view_src:
        xr, yr = canvas.xview()[0], canvas.yview()[0]  # remember x, y for result image before switch to source
        ShowPreview(preview_src, 'Source')  # switch to source
        canvas.xview_moveto(xs)  # restore x, y for source image after switch to source
        canvas.yview_moveto(ys)
    else:
        xs, ys = canvas.xview()[0], canvas.yview()[0]  # remember x, y for source image before switch to result
        ShowPreview(preview_filtered, 'Result')  # switch to result
        canvas.xview_moveto(xr)  # restore x, y for result image after switch to result
        canvas.yview_moveto(yr)


def GetSource(event=None) -> None:
    """Open source image and redefine other controls state."""

    global zoom_factor, view_src, is_filtered, is_saved, info_normal, color_mode_str
    global preview, preview_src, preview_filtered  # preview and copies of preview
    global sourcefilename, X, Y, Z, maxcolors, source_image, info
    global XNEW, YNEW, result_image

    old_sourcefilename = sourcefilename  # Temporary saving info in case of "Open.." cancel
    old_size = (X, Y, Z)
    sourcefilename = askopenfilename(title='Open image file', filetypes=[('Supported formats', '.png .ppm .pgm .pbm .pnm'), ('Portable network graphics', '.png'), ('Portable any map', '.ppm .pgm .pbm .pnm')])
    if sourcefilename == '':
        sourcefilename = old_sourcefilename
        X, Y, Z = old_size
        return

    # ↓ Next must be set AFTER "sourcefilename", in case of "Open.." cancel
    zoom_factor = 0
    view_src = True
    is_filtered = False
    is_saved = True

    UIBusy()

    if Path(sourcefilename).suffix.lower() == '.png':
        # ↓ Reading PNG image as list
        X, Y, Z, maxcolors, source_image, info = png2list(sourcefilename)

    elif Path(sourcefilename).suffix.lower() in ('.ppm', '.pgm', '.pbm', '.pnm'):
        # ↓ Reading PNM image as list
        X, Y, Z, maxcolors, source_image = pnm2list(sourcefilename)
        # ↓ Creating dummy info required to correctly Save As PNG later.
        #   Fixing color mode, the rest is fixed with pnglpng v. 25.01.07.
        info = {'bitdepth': 16} if maxcolors > 255 else {'bitdepth': 8}

    else:
        raise ValueError('Extension not recognized')

    XNEW, YNEW = (X, Y)

    """ ┌────────────────────────────────────────────┐
        │ Creating deep copy of source 3D list       │
        │ to avoid accumulating repetitive filtering │
        └────────────────────────────────────────────┘ """
    result_image = deepcopy(source_image)

    """ ┌───────────────┐
        │ Viewing image │
        └───────────────┘ """
    # ↓ Converting list to bytes of PNM-like structure "preview_data" in memory
    preview_data = list2bin(result_image, maxcolors, show_chessboard=True)
    # ↓ Now generating preview from "preview_data" bytes using Tkinter
    preview = PhotoImage(data=preview_data)

    # ↓ Creating copy of source preview for further
    #   fast switch between source and result.
    preview_src = preview_filtered = preview

    # ↓ Calculate zoom factor for "Zoom to fit".
    if preview.width() > sortir.winfo_screenwidth() or (128 + preview.height() + frame_top.winfo_reqheight()) > sortir.winfo_screenheight():
        zoom_factor = max(-max(preview.width() // sortir.winfo_screenwidth(), (128 + preview.height() + frame_top.winfo_reqheight() + frame_zoom.winfo_reqheight() + info_string.winfo_reqheight()) // sortir.winfo_screenheight()), minizoom)

    # ↓ Finally the show part
    ShowPreview(preview, 'Source')

    # ↓ Binding preview mouse drag
    zanyato.bind('<Motion>', canvasCoord)
    zanyato.bind('<B1-Motion>', canvasDrag)
    zanyato.bind('<ButtonRelease-1>', lambda event: canvas.config(cursor='arrow'))  # cursor back after drag
    # ↓ Binding preview click
    zanyato.bind('<Control-Button-1>', zoomIn)  # Ctrl + left click
    zanyato.bind('<Double-Control-Button-1>', zoomIn)  # Ctrl + left click too fast
    zanyato.bind('<Control-+>', zoomIn)
    zanyato.bind('<Control-=>', zoomIn)
    zanyato.bind('<Alt-Button-1>', zoomOut)  # Alt + left click
    zanyato.bind('<Double-Alt-Button-1>', zoomOut)  # Alt + left click too fast
    zanyato.bind('<Control-minus>', zoomOut)
    zanyato.bind('<Control-Key-1>', zoomOne)
    zanyato.bind('<Control-Alt-Key-0>', zoomOne)
    # ↓ Binding global
    sortir.bind('<MouseWheel>', zoomWheel)  # Wheel scroll
    sortir.bind('<Control-i>', ShowInfo)
    sortir.bind('<Return>', RunFilter)
    # ↓ ↓ Spinbox mouse input
    in01.unbind('<MouseWheel>')
    in01.bind('<MouseWheel>', incWheel)
    # ↓ Info in menu
    menu02.entryconfig('Image Info...', state='normal')
    # ↓ Enabling 'Save as...'
    menu02.entryconfig('Save as...', state='normal')
    sortir.bind_all('<Control-Shift-S>', SaveAs)
    # ↓ Enabling zoom buttons
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
    # ↓ "Filter" mouseover
    butt_filter.bind('<Enter>', lambda event=None: butt_filter.config(foreground=butt['activeforeground'], background=butt['activebackground']))
    butt_filter.bind('<Leave>', lambda event=None: butt_filter.config(foreground=butt['foreground'], background=butt['background']))
    # ↓ Entry mouseovers
    in01.bind('<Enter>', lambda event=None: in01.config(foreground=butt['activeforeground'], background=butt['activebackground']))
    in01.bind('<Leave>', lambda event=None: in01.config(foreground=butt['foreground'], background='white'))
    UINormal()
    UIFit()
    sortir.geometry(f'+{(sortir.winfo_screenwidth() - sortir.winfo_width()) // 2}+64')
    zanyato.focus_set()


def RunFilter(event=None) -> None:
    """Filter image, then preview result."""

    global view_src, is_filtered, is_saved, info_normal, timing
    global preview_filtered
    global XNEW, YNEW, result_image
    global xs, xr, ys, yr  # view point coordinates in *s*ource and *r*esult image

    xs, ys = canvas.xview()[0], canvas.yview()[0]

    # ↓ filtering parameters
    if method_str.get() == 'Bilinear':
        method = 'bilinear'
    elif method_str.get() == 'Barycentric':
        method = 'barycentric'

    if edge_str.get() == 'Repeat':
        edge = 'repeat'
    elif edge_str.get() == 'Wrap':
        edge = 'wrap'
    else:
        edge = 0

    UIBusy()

    """ ╭────────────────────────────╮
        │ Rotation using algorithmic │
        │ displacement map. ╭────────╯
        ╰───────────────────╯ """

    SIN = sin(radians(ini_x.get()))
    COS = cos(radians(ini_x.get()))

    XNEW = int(abs(X * COS) + abs(Y * SIN))
    YNEW = int(abs(X * SIN) + abs(Y * COS))

    def fx(x, y):
        return ((x - XNEW / 2) * COS) - ((y - YNEW / 2) * SIN) + X / 2

    def fy(x, y):
        return ((x - XNEW / 2) * SIN) + ((y - YNEW / 2) * COS) + Y / 2

    # ↓ Rotation using `displace` from `imin.displace`
    start = time()
    result_image = displace(source_image, fx, fy, XNEW, YNEW, edge=edge, method=method)
    timing = time() - start

    """
    # ↓ Alternative rotation using `pixel` from `imin`
    from imin import pixel
    start = time()
    result_image = [[pixel(source_image, fx(x, y), fy(x, y), edge=edge, method=method) for x in range(XNEW)] for y in range(YNEW)]
    timing = time() - start
    """

    # ↓ preview result
    preview_data = list2bin(result_image, maxcolors, show_chessboard=True)
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
    # ↓ binding source/result switch
    #   (on click works silly with drag)
    # zanyato.bind('<Button-1>', SwitchView)
    # zanyato.bind('<ButtonRelease-1>', SwitchView)
    zanyato.bind('<space>', SwitchView)  # # "Space" key. May be worth binding whole sortir?
    # ↓ Adding filename, mode and status to window title a-la Photoshop
    sortir.title(f'{product_name}: {Path(sourcefilename).name}{color_mode_str}{"*" if is_filtered else ""}')
    info_normal = {'txt': f'{Path(sourcefilename).name}{"*" if is_filtered else ""} X={XNEW if is_filtered else X} Y={YNEW if is_filtered else Y} Z={Z} maxcolors={maxcolors}', 'fg': 'grey', 'bg': 'grey90'}
    UINormal()
    zanyato.focus_set()  # moving focus to preview


def zoomIn(event=None) -> None:
    """Zoom preview in."""

    global zoom_factor

    zoom_factor = min(zoom_factor + 1, maxizoom)  # max zoom 5

    if view_src:
        ShowPreview(preview_src, 'Source')
    else:
        ShowPreview(preview_filtered, 'Result')

    # ↓ reenabling +/- buttons
    butt_minus.config(state='normal', cursor='hand2')
    if zoom_factor == maxizoom:  # max zoom 5
        butt_plus.config(state='disabled', cursor='arrow')
    else:
        butt_plus.config(state='normal', cursor='hand2')
    UIFit()
    sortir.update()


def zoomOut(event=None) -> None:
    """Zoom preview out."""

    global zoom_factor

    zoom_factor = max(zoom_factor - 1, minizoom)  # min zoom 1/10

    if view_src:
        ShowPreview(preview_src, 'Source')
    else:
        ShowPreview(preview_filtered, 'Result')

    # ↓ reenabling +/- buttons
    butt_plus.config(state='normal', cursor='hand2')
    if zoom_factor == minizoom:  # min zoom 1/10
        butt_minus.config(state='disabled', cursor='arrow')
    else:
        butt_minus.config(state='normal', cursor='hand2')
    UIFit()
    sortir.update()


def zoomOne(event=None) -> None:
    """Zoom 1:1."""

    global zoom_factor

    zoom_factor = 0

    if view_src:
        ShowPreview(preview_src, 'Source')
    else:
        ShowPreview(preview_filtered, 'Result')

    # ↓ reenabling +/- buttons
    butt_plus.config(state='normal', cursor='hand2')
    butt_minus.config(state='normal', cursor='hand2')
    UIFit()
    sortir.update()


def zoomWheel(event) -> None:
    """zoomIn or zoomOut by mouse wheel."""

    if event.widget not in transparent_controls:
        if event.delta < 0:
            zoomOut()
        if event.delta > 0:
            zoomIn()


def onSave() -> None:
    """Reassign images and other objects from new to old upon saving."""

    global preview_src, info_normal
    global sourcefilename, X, Y, Z, maxcolors, source_image

    # ↓ saved file becomes new source file
    sourcefilename = resultfilename
    source_image = result_image
    preview_src = preview_filtered
    X, Y = (XNEW, YNEW)

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

    global is_filtered, is_saved
    global resultfilename

    if is_saved:  # block repetitive saving
        return
    if not is_filtered:  # block useless source resaving
        return
    resultfilename = sourcefilename
    UIBusy()
    # ↓ Save format choice
    if Path(resultfilename).suffix.lower() == '.png':
        info['compression'] = 9  # Explicitly setting compression
        list2png(resultfilename, result_image, info)  # Writing file
    elif Path(resultfilename).suffix.lower() in ('.ppm', '.pgm', '.pnm'):
        list2pnm(resultfilename, result_image, maxcolors)  # Writing file
    # ↓ Flagging image as saved, not filtered
    is_saved = True  # to block future repetitive saving
    is_filtered = False
    # ↓ Now saved file becomes new source file
    onSave()
    UINormal()


def SaveAs(event=None) -> None:
    """Once pressed on Save as..."""

    global is_saved, is_filtered
    global resultfilename

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
        return
    UIBusy()
    # ↓ Save format choice
    if Path(resultfilename).suffix.lower() == '.png':
        info['compression'] = 9  # Explicitly setting compression
        list2png(resultfilename, result_image, info)  # Writing file
    elif Path(resultfilename).suffix.lower() in ('.ppm', '.pgm'):
        list2pnm(resultfilename, result_image, maxcolors)  # Writing file
    else:
        raise ValueError('Extension not recognized')
    # ↓ Flagging image as saved, not filtered, and disabling "Save"
    is_saved = True  # to block future repetitive saving
    is_filtered = False
    # ↓ Now saved file becomes new source file
    onSave()
    UINormal()


def valiDig(new_value):
    """Tries to validate float input. Far from being perfect yet."""

    return new_value == '' or new_value == '-' or new_value.replace('.', '').replace(' ', '').isdigit()


def incWheel(event) -> None:
    """Increment or decrement spinboxes by mouse wheel."""

    if event.widget == in01:
        if event.delta < 0:
            ini_x.set(ini_x.get() - 1)
        if event.delta > 0:
            ini_x.set(ini_x.get() + 1)


""" ╔═══════════╗
    ║ Main body ║
    ╚═══════════╝ """
# ↓ Initializing
sourcefilename = ''
X = Y = Z = 0
zoom_factor = 0
view_src = True
is_filtered = False
timing = None
product_name = 'Rev⥀lver'  # ↺
minizoom, maxizoom = (-4, 9)  # Zoom from 1:5 to 10:1

sortir = Tk()

sortir.iconphoto(True, PhotoImage(data='P6\n3 3\n255\n'.encode(encoding='ascii') + randbytes(3 * 3 * 3)))
sortir.title(product_name)

validate_entry = sortir.register(valiDig)

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

# ↓ Info statuses dictionaries
info_normal = {'txt': f'{product_name} {__version__}', 'fg': 'grey', 'bg': 'grey90'}
info_busy = {'txt': 'BUSY, PLEASE WAIT', 'fg': 'red', 'bg': 'yellow'}
color_mode_str = ' '
# ↓ Info string
info_string = Label(sortir, text=info_normal['txt'], font=('courier', 7), foreground=info_normal['fg'], background=info_normal['bg'], relief='groove')
info_string.pack(side='bottom', padx=0, pady=(2, 0), fill='both')

""" ┌──────────────────────┐
    │ Top frame (controls) │
    └─────────────────────-┘ """
frame_top = Frame(sortir, borderwidth=2, relief='groove')
frame_top.pack(side='top', anchor='w', pady=(0, 2))

col = 0

# ↓ File menubutton
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
butt_file.grid(row=0, column=col, rowspan=2, sticky='n', padx=(0, 10), pady=0)
col += 1

# ↓ "File..." menu
menu02 = Menu(butt_file, tearoff=False)
menu02.add_command(label='Open...', state='normal', command=GetSource, accelerator='Ctrl+O')
menu02.add_separator()
menu02.add_command(label='Save', state='disabled', command=Save, accelerator='Ctrl+S')
menu02.add_command(label='Save as...', state='disabled', command=SaveAs, accelerator='Ctrl+Shift+S')
menu02.add_separator()
menu02.add_command(label='Image Info...', accelerator='Ctrl+I', state='disabled', command=ShowInfo)
menu02.add_separator()
menu02.add_command(label='Exit', state='normal', command=DisMiss, accelerator='Ctrl+Q')

butt_file['menu'] = menu02

butt_file.focus_set()  # Setting focus to "File..."

# ↓ Filter section begins
info01 = Label(frame_top, text='Angle', font=('helvetica', 11), state='disabled')
info01.grid(row=0, column=col)
col += 1

# ↓ Angle value
ini_x = DoubleVar(value=0.0)
in01 = Spinbox(
    frame_top,
    from_=-90.0,
    to=90.0,
    increment=1,
    textvariable=ini_x,
    format='%2.1f',
    state='disabled',
    width=4,
    font=('helvetica', 11),
    foreground=butt['foreground'],
    background='white',
    validate='key',
    validatecommand=(validate_entry, '%S'),
)
in01.grid(row=0, column=col)
col += 1

# ↓ Interpolation method
method_str = StringVar(value='Bilinear')
method_menu = OptionMenu(
    frame_top,
    method_str,
    *[
        'Bilinear',
        'Barycentric',
    ],
)
method_menu.grid(row=0, column=col)
method_menu.configure(indicatoron=True, font=('helvetica', 12), width=9, anchor='e', relief=butt['relief'], activebackground=butt['activebackground'], state='disabled')
method_menu['menu'].configure(font=method_menu['font'])

# ↓ Edge mode
edge_str = StringVar(value='Zero')
edge_menu = OptionMenu(
    frame_top,
    edge_str,
    *[
        'Zero',
        'Repeat',
        'Wrap',
    ],
)
edge_menu.grid(row=1, column=col)
edge_menu.configure(indicatoron=True, font=('helvetica', 12), width=9, anchor='e', relief=butt['relief'], activebackground=butt['activebackground'], state='disabled')
edge_menu['menu'].configure(font=edge_menu['font'])

col += 1

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
butt_filter.grid(row=0, column=col, rowspan=2, sticky='n', padx=(10, 0), pady=0)

""" ┌──────────────────────────────┐
    │ Center frame (image preview) │
    └─────────────────────────────-┘ """
frame_preview = Frame(sortir, borderwidth=2, relief='groove')
frame_preview.pack(side='top', anchor='center', expand=True)

canvas = Canvas(
    frame_preview,
    borderwidth=1,
    highlightthickness=1,
)
canvas.pack()

zanyato = Label(
    canvas,
    text='Preview area.\n  Double click to open image,\n  Right click or Alt+F for a menu.\nWith image opened,\n  Ctrl+Click to zoom in,\n  Alt+Click to zoom out,\n  Enter to filter.\nWhen filtered, click or Space bar\nto switch source/result.',
    font=('helvetica', 12),
    justify='left',
    padx=24,
    pady=24,
    borderwidth=2,
    background='grey90',
    relief='groove',
)
zanyato.pack(side='top')

zanyato_ = canvas.create_window(
    0,
    0,
    window=zanyato,
    width=zanyato.winfo_reqwidth(),
    height=zanyato.winfo_reqheight(),
    anchor='nw',
)
canvas.config(
    width=zanyato.winfo_reqwidth(),
    height=zanyato.winfo_reqheight(),
    scrollregion=(0, 0, zanyato.winfo_reqwidth(), zanyato.winfo_reqheight()),
)

frame_zoom = Frame(frame_preview, borderwidth=2, relief='groove')
frame_zoom.pack(side='bottom')

butt_plus = Button(frame_zoom, text='+', font=('courier', 8), width=2, cursor='arrow', state='disabled', borderwidth=1, command=zoomIn)
butt_plus.pack(side='left', padx=0, pady=0, fill='both')

butt_minus = Button(frame_zoom, text='-', font=('courier', 8), width=2, cursor='arrow', state='disabled', borderwidth=1, command=zoomOut)
butt_minus.pack(side='right', padx=0, pady=0, fill='both')

label_zoom = Label(frame_zoom, text='Zoom 1:1', font=('courier', 8), state='disabled')
label_zoom.pack(side='left', anchor='n', padx=2, pady=0, fill='both')

transparent_controls = (in01,)  # To be cut off global events

""" ┌─────────────────────────────────────────────┐
    │ Binding everything that does not need image │
    └────────────────────────────────────────────-┘ """
# ↓ Info string binding for displaying execution time
info_string.bind('<Enter>', lambda event=None: info_string.config(text=f'Run time: {timing}'))
info_string.bind('<Leave>', lambda event=None: info_string.config(text=info_normal['txt']))
info_string.bind('<Control-Button-1>', lambda event=None: [sortir.clipboard_clear(), sortir.clipboard_append(f'{timing}\n')])
# ↓ "File..." mouseover
butt_file.bind('<Enter>', lambda event=None: butt_file.config(relief=butt['overrelief']))
butt_file.bind('<Leave>', lambda event=None: butt_file.config(relief=butt['relief']))
# ↓ Double-click image area to "Open..."
zanyato.bind('<Double-Button-1>', GetSource)
frame_preview.bind('<Double-Button-1>', GetSource)
# ↓ Whole sortir binding menu, "Open..." and "Exit"
sortir.bind_all('<Button-3>', ShowMenu)  # Popup menu
sortir.bind_all('<Alt-f>', ShowMenu)
sortir.bind_all('<Alt-F>', ShowMenu)
sortir.bind_all('<Control-o>', GetSource)
sortir.bind_all('<Control-O>', GetSource)
sortir.bind_all('<Control-q>', DisMiss)
sortir.bind_all('<Control-Q>', DisMiss)
sortir.bind_all('<Control-w>', DisMiss)
sortir.bind_all('<Control-W>', DisMiss)

# ↓ Center window horizontally, +100 vertically
sortir.update()
# print(sortir.winfo_width(), sortir.winfo_height())
UIFit()
sortir.maxsize(9 * sortir.winfo_screenwidth() // 10, 9 * sortir.winfo_screenheight() // 10)
sortir.geometry(f'+{(sortir.winfo_screenwidth() - sortir.winfo_width()) // 2}+64')

sortir.mainloop()
