# Barycentric and bilinear image interpolation in pure Python

## Overview

Currently **imin** repository contains code for barycentric and bilinear image interpolation.

[Bilinear image interpolation](https://en.wikipedia.org/wiki/Bilinear_interpolation) works by considering pixel as ■ square, and performing interpolation between four corners.

Barycentric image interpolation, the most interesting part of the module, works by dividing ■ pixel square onto either ◤◢ or ◣◥ subtriangles, and performing interpolation within a triangle using [barycentric coordinates](https://en.wikipedia.org/wiki/Barycentric_coordinate_system).

This branch, **"Functional"**, specifically, contain **imin** module version to be used as functions, not classes, and several shell applications to show the module in action.

## Figures

Some illustrations of difference between bilinear and barycentric interpolations are given below.

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

Module **imin**:

- **`__init__.py`**: This is not just an init file. Actually, it contains all code required to read image pixel at float coordinates, interpolated from surrounding pixels using either barycentric or bilinear method. If reading image pixels is all you need, you may copy `__init__.py` file alone and use it for your applications. Remember that I don't give a care to legal stuff, so you can use my code for free, completely or partially, and modify at will.
- **`displace.py`**: General purpose image displacement using either barycentric or bilinear interpolation. Exact type of displacement is controlled by fx(x, y) and fy(x, y) functions, given to `displace` as arguments.
- **`rescale.py`**: Image rescaling. Obviously, image rescaling is a specific case of displacement, and can be done with displacer, but specific case of rescaling gives a chance to add some specific speed optimization; therefore a separate code was created.

Instructions for developers on module usage and function input syntax are given in a rather prolific docstrings. Also, you may always take a look at the source of sample GUI shell applications, listed below.

Shell applications:

- **`distorter.py`**: the main part of demo. Distorter provides examples of general purpose image displacer (`displace.py`) usage. Currently demo includes only two functions: linear skewing and wave-like deformation with sine function;
- **`mdbiggener.py`**: image rescaler; provides a demo for `rescale.py`;
- **`revolver.py`**: image rotation program. Based entirely on `displace.py`, and separated as specific program just because rotation GUI should take only one argument (i.e. angle), while displacement currently takes two (one for x and other for y). To avoid making a program with only half of GUI being functional, this particular example program was created.

> [!NOTE]
> Shell programs GUI is rather clumsy, yet provides some suitable features. For example, with mouse over numerical input fields you can use mouse wheel to gradually increment/decrement input values. Mouse over info string below image shows you last filter execution time (and Ctrl+Click on it places this value to clipboard. This was made to simplify speed tests during optimization).

Shell programs GUI provides whole set of interpolation options; however, they do not always work as one may expect. For example, "Wrap around" processing for seamless textures in "Distorter" works for wave deformation, but makes seams for skewing. This is caused by skewing nature: opposite image borders slide against each other, thus breaking seamless borders match. Please remember that these shell programs are made for module testing and illustration purposes, and not as a complete replacement for Photoshop or GIMP.

| Displacer GUI |
| :---: |
| [![Displacer GUI](https://dnyarri.github.io/imin/anigui.png "Displacer in action, barycentric image interpolation in wrap around mode")](https://dnyarri.github.io/imin.html) |

## Links

[Barycentric and bilinear image interpolation explanatory page](https://dnyarri.github.io/imin.html "Barycentric and bilinear image interpolation in pure Python - explanatory page")

[Barycentric and bilinear image interpolation source code at Github](https://github.com/Dnyarri/imin "Barycentric and bilinear image interpolation in pure Python - source code at Github")

[Barycentric and bilinear image interpolation source code at Gitflic mirror](https://gitflic.ru/project/dnyarri/imin "Barycentric and bilinear image interpolation in pure Python - source code at Gitflic")

[Dnyarri website - more Python freeware for image processing and 3D](https://dnyarri.github.io "The Toad's Slimy Mudhole - Python freeware for POV-Ray and other 3D, Scale2x, Scale3x, Scale2xSFX, Scale2xSFX, PPM and PGM image support, bilinear and barycentric image interpolation, and batch processing") by the same author.
