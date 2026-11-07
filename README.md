# Barycentric and bilinear image interpolation in pure Python

## Overview

Currently **imin** repository contains code for barycentric and bilinear image interpolation using pure Python. Free-threaded Python is highly recommended.

> [!WARNING]
>
> The code is evolutionary structured (*i.e.* hard to understand), sparingly documented, *und highly dangerous! © Professor Professor*.

[Bilinear image interpolation](https://en.wikipedia.org/wiki/Bilinear_interpolation) works by considering pixel as ⬛ square, and performing interpolation between four corners.

Barycentric image interpolation, the most interesting part of the module, works by dividing ⬛ pixel square onto either ◤◢ or ◣◥ subtriangles, and performing interpolation within a triangle using [barycentric coordinates](https://en.wikipedia.org/wiki/Barycentric_coordinate_system).

## Objectable branch

This branch, **"Objectable"**, specifically, contain **imin** module version to be used as objects, i.e. class, and several shell applications to show the module in action. **Imin** version designed as functions, not a class, is contained in [**"Functional"**](https://github.com/Dnyarri/imin/tree/functional) branch.

> [!NOTE]
>
> Although English is not my native language, I *do* know potential meaning of *"Objectable"* word. Any word misuse encountered hereinafter is strictly intentional.

To avoid import conflicts, files belonging to **imin** module, **"Objectable"** version, are placed inside `imino` folder.

## Figures

Some illustrations of difference between bilinear and barycentric interpolation are given below.

| Source | Bilinear interpolation | Barycentric interpolation |
| :---: | :---: | :---: |
| ![Source image](https://dnyarri.github.io/imin/peak3.png "Source image 3x3 px") | ![Bilinear interpolation](https://dnyarri.github.io/imin/peak3bil.png "Bilinear upscale x20 times") | ![Barycentric interpolation](https://dnyarri.github.io/imin/peak3bar.png "Barycentric upscale x20 times") |
| Source image 3x3 px | Bilinear upscale x20 times | Barycentric upscale x20 times |

Above you can see an example of upscaling a single black pixel over white background 20 times. Surely 20 times figure is impractical, but gives a good illustration of interpolation methods.

| Source | Bilinear interpolation | Barycentric interpolation |
| :---: | :---: | :---: |
| ![Source image](https://dnyarri.github.io/imin/eye16.png "Source image 22x16 px") | ![Bilinear interpolation](https://dnyarri.github.io/imin/eye16bil.png "Bilinear upscale x5 times") | ![Barycentric interpolation](https://dnyarri.github.io/imin/eye16bar.png "Barycentric upscale x5 times") |
| Source image 22x16 px | Bilinear upscale x5 times | Barycentric upscale x5 times |

Above you can see an example of upscaling a photo fragment 5 times. It seems that barycentric interpolation produces clearer general eye shape appearance, but turns single pixel pupil into rhomb, while bilinear interpolation simply blurs everything.

## Files

### Module **imin**

- **`__init__.py`**: Beside being an init file, it contains code required to read image pixel at float coordinates. Code for processing whole image, not just reading a pixel, is contained in other files, mentioned below.
- **`displace.py`**: General purpose image displacement using either barycentric or bilinear interpolation. Exact type of displacement is controlled by fx(x, y) and fy(x, y) functions, given to `displace` as arguments.
- **`rescale.py`**: Image rescaling. Obviously, image rescaling is a specific case of displacement, and can be done with displacer, but specific case of rescaling gives a chance to add some specific speed optimization; therefore a separate code was created.

Instructions for developers on module usage and function input syntax are given in a rather prolific docstrings. Also, you may always take a look at the source of sample GUI shell applications, listed below.

### Shell applications

- **`mdbiggener.py`**: image rescaler; provides a demo for `rescale.py`;

  | Fig. 1. *Image rescaler with configurable interpolation* |
  | :---: |
  | [![Embiggener GUI](https://dnyarri.github.io/imin/embiggener.webp "Image rescaler with barycentric interpolation")](https://dnyarri.github.io/imin.html) |
  | *Sample program "Em⇅Debiggener".* GUI is rather compact yet provides some suitable features - draggable canvas with Photoshop-like zooming by mouse, *etc.* |

- **`distorter.py`**: the main part of demo. Distorter provides examples of using general purpose image displacer (`displace.py`) with various algorithmic displacement functions. Currently demo includes a few functions:
  - skewing (tangent based);
  - wavy distortion (sine based);
  - a couple of toothy distortions (modulo based).

  | Fig. 2. *Image displacement in "wrap around" mode, using barycentric image interpolation* |
  | :---: |
  | [![Distorter GUI](https://dnyarri.github.io/imin/distorter.webp "Displacer in action, barycentric image interpolation in wrap around mode")](https://dnyarri.github.io/imin.html) |
  | *Sample program "Dist◇rter", performing arbitrary image displacement in "wrap around" mode, using barycentric image interpolation.* |

- **`revolver.py`**: image rotation program. Based entirely on `displace.py`, and separated as specific program just because rotation GUI should take only one argument (i.e. angle), while displacement currently takes two (one for x and other for y). To avoid making a program with only half of GUI being functional, this particular example program was created.

Shell programs GUI provides whole set of interpolation and extrapolation options; however, they do not always work as one may expect. For example, "Wrap around" processing for seamless textures in "Distorter" works for wave deformation, but makes seams for skewing. This is caused by skewing nature: opposite image borders slide against each other, thus breaking seamless borders match.

Please remember that these shell programs are made mostly for module testing and illustration purposes, rather than a replacement for Photoshop or GIMP.

## Prerequisite and Dependencies

1. [Python](https://www.python.org/ "CPython") 3.11 or above. Note that during November 2026 module was rewritten to support multithreading, which provides dramatic speed increase when running under free-threaded (no GIL) Python; therefore using modern versions, like Python 3.14 and above, is **highly recommended**.
2. [PyPNG](https://gitlab.com/drj11/pypng "Pure Python PNG format module"). Required for [PNG images reading and writing](https://drj11.gitlab.io/pypng "PyPNG docs"). Copy included into current **imin** distribution.
3. [PyPNM](https://pypi.org/project/PyPNM/ "Pure Python PPM and PGM format module"). Required for [viewing image data, as well as PPM and PGM images reading and writing](https://dnyarri.github.io/pypnm.html "PyPNM provides viewing image data, as well as PPM and PGM images reading and writing"). Copy included into current **imin** distribution.
4. Tkinter. Normally included into standard CPython distribution.

## Links

[Barycentric and bilinear image interpolation explanatory page with illustrations](https://dnyarri.github.io/imin.html "Barycentric and bilinear image interpolation in pure Python - explanatory page with illustrations")

[Barycentric and bilinear image interpolation source code at Github](https://github.com/Dnyarri/imin "Barycentric and bilinear image interpolation in pure Python - source code at Github")

[Barycentric and bilinear image interpolation source code at Gitflic mirror](https://gitflic.ru/project/dnyarri/imin "Barycentric and bilinear image interpolation in pure Python - source code at Gitflic")

[The Toad's Slimy Mudhole website - more Python freeware for 2D image processing, POV-Ray and other 3D, and batch automation](https://dnyarri.github.io "The Toad's Slimy Mudhole - Python freeware for POV-Ray and other 3D, Scale2x, Scale3x, Scale2xSFX, Scale3xSFX, PPM and PGM image support, bilinear and barycentric image interpolation, PNG to ICO conversion, and batch processing") by the same author.
