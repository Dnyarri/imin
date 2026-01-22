# Barycentric and bilinear image interpolation in pure Python

## Overview

Currently **imin** repository contains code for barycentric and bilinear image interpolation.

[Bilinear image interpolation](https://en.wikipedia.org/wiki/Bilinear_interpolation) works by considering pixel as ■ square, and performing interpolation between four corners.

Barycentric image interpolation, the most interesting part of the module, works by dividing ■ pixel square onto either ◤◢ or ◣◥ subtriangles, and performing interpolation within a triangle using [barycentric coordinates](https://en.wikipedia.org/wiki/Barycentric_coordinate_system).

This branch, **"Functional"**, specifically, contain **imin** module version to be used as functions, not classes, and several shell applications to show the module in action.

## Content

Module **imin**:

- **`__init__.py`**: This is not just an init file. Actually, it contains all code required to read image pixel at float coordinates, interpolated from surrounding pixels using either barycentric or bilinear method. If reading image pixels is all you need, you may copy `__init__.py` file alone and use it for your applications. Remember that I don't give a care to legal stuff, so you can use my code for free, completely or partially, and modify at will.
- **`displace.py`**: General purpose image displacement using either barycentric or bilinear interpolation. Exact type of displacement is controlled by fx(x, y) and fy(x, y) functions, given to `displace` as arguments.
- **`rescale.py`**: Image rescaling. Obviously, image rescaling is a specific case of displacement, and can be done with displacer, but specific case of rescaling gives a chance to add some specific speed optimization; therefore a separate code was created.

Shell applications:

- **`distorter.py`**: the main part of demo. Distorter provides examples of general purpose image displacer (`displace.py`) usage. Currently demo includes only two functions: linear skewing and wave-like deformation with sine function;
- **`mdbiggener.py`**: image rescaler; provides a demo for `rescale.py`;
- **`revolver.py`**: image rotation program. Based entirely on `displace.py`, and separated as specific program just because rotation GUI should take only one argument (i.e. angle), while displacement currently takes two (one for x and other for y). To avoid making a program with only half of GUI being functional, this particular example program was created.

> [!NOTE]
> Shell programs GUI is rather clumsy, yet provides some suitable features. For example, with mouse over numerical input fields you can use mouse wheel to gradually increment/decrement input values. Mouse over info string below image shows you last filter execution time (and Ctrl+Click on it places this value to clipboard. This was made to simplify speed tests during optimization).

Shell programs GUI provides whole set of interpolation options; however, they do not always work as one may expect. For example, "Wrap around" processing for seamless textures in "Distorter" works for wave deformation, but makes seams for skewing. This is caused by skewing nature: opposite image borders slide against each other, thus breaking seamless borders match. Please remember that these shell programs are made for module testing and illustration purposes, and not as a complete replacement for Photoshop or GIMP.

## Links

[Barycentric and bilinear image interpolation page](https://dnyarri.github.io/imin.html "Barycentric and bilinear image interpolation in pure Python - starting page")

[Barycentric and bilinear image interpolation source at Github](https://github.com/Dnyarri/imin "Barycentric and bilinear image interpolation in pure Python - source code at Github")

[Barycentric and bilinear image interpolation source at Gitflic mirror](https://gitflic.ru/project/dnyarri/imin "Barycentric and bilinear image interpolation in pure Python - source code at Github")

[Dnyarri website - more Python freeware](https://dnyarri.github.io "The Toad's Slimy Mudhole - Python freeware for POV-Ray and other 3D, Scale2x, Scale3x, Scale2xSFX, Scale2xSFX, PPM and PGM image support, bilinear and barycentric image interpolation, and batch processing") by the same author.
