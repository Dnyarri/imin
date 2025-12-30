#!/usr/bin/env python3

"""Bilinear image interpolation and rescaling."""

__author__ = 'Ilya Razmanov'
__copyright__ = '(c) 2024-2025 Ilya Razmanov'
__credits__ = 'Ilya Razmanov'
__license__ = 'unlicense'
__version__ = '25.11.25.19'
__maintainer__ = 'Ilya Razmanov'
__email__ = 'ilyarazmanov@gmail.com'
__status__ = 'Development'

from functools import lru_cache
from operator import mul


def pixel(image3d: list[list[list[int]]], x: int | float, y: int | float, edge: int = 1) -> list[int]:
    """Getting whole pixel from image list, nearest neighbour interpolation,
    returns list[channel] for pixel(x, y).

    :param image3d: source image 3D list, coordinate system match Photoshop,
    i.e. origin is top left corner, channels order LA or RGBA from bottom to top;
    :type image3d: list[list[list[int]]]
    :param int or float x: x coordinate of pixel being read;
    :param int or float y: y coordinate of pixel being read;
    :param int edge: edge extrapolation mode:

        - edge=1: repeat edge, like Photoshop;
        - edge=2: wrap around;
        - edge=other: extrapolate with zeroes. Alpha=0 correspond to transparent.
    :return: pixel value as list of channel values.
    :rtype: list[int]

    """

    # ↓ Determining source image sizes.
    Y = len(image3d)
    X = len(image3d[0])
    Z = len(image3d[0][0])

    if edge == 1:
        # ↓ Repeat edge.
        cx = min((X - 1), max(0, int(x)))
        cy = min((Y - 1), max(0, int(y)))
        pixelvalue = image3d[cy][cx]
    elif edge == 2:
        # ↓ Wrap around.
        cx = int(x) % X
        cy = int(y) % Y
        pixelvalue = image3d[cy][cx]
    else:
        # ↓ Zeroes. Fortunately A=0 correspond to transparent.
        if x < 0 or y < 0 or x > X - 1 or y > Y - 1:
            pixelvalue = [0] * Z
        else:
            pixelvalue = image3d[int(y)][int(x)]

    return pixelvalue


def blin(image3d: list[list[list[int]]], x: float, y: float, edge: int) -> list[int]:
    """Returns bilinearly interpolated pixel(x, y).

    :param image3d: source image 3D list, coordinate system match Photoshop,
    i.e. origin is top left corner, channels order LA or RGBA from bottom to top;
    :type image3d: list[list[list[int]]]
    :param float x: x coordinate of pixel being read;
    :param float y: y coordinate of pixel being read;
    :param int edge: edge extrapolation mode:

        - edge=1: repeat edge, like Photoshop;
        - edge=2: wrap around;
        - edge=other: extrapolate with zeroes. Alpha=0 correspond to transparent.
    :return: interpolated pixel(x, y) value.
    :rtype: list[int]

    """

    def _intaddup(a, b, c, d):
        return int(a + b + c + d)

    # ↓ Determining source image sizes.
    #   Y = len(image3d)
    #   X = len(image3d[0])
    Z = len(image3d[0][0])

    """ Square corners are enumerated according to scheme below:

          x0   x1
        ┼────┼────┤
     y0 │ 00 │ 10 │
        ┼────┼────┤
     y1 │ 01 │ 11 │
        └────┴────┘
    NOTE: Corners coordinates are calculated taking into account that
    for negative x and y values
        int(x) > x
            and
        int(y) > y
        correspondingly. """

    if x >= 0:
        x0 = int(x)
    else:
        x0 = int(x) - 1
    if y >= 0:
        y0 = int(y)
    else:
        y0 = int(y) - 1
    # ↓ In case of direct hit, no interpolation required
    if x == x0 and y == y0:
        return pixel(image3d, x0, y0, edge)
    # ↓ When direct hit misses, interpolation goes on
    x1 = x0 + 1
    y1 = y0 + 1

    # ↓ Distance weights for pixels, packed as tuple for map() below
    wt00 = (((x1 - x) * (y1 - y)),) * Z
    wt01 = (((x1 - x) * (y - y0)),) * Z
    wt10 = (((x - x0) * (y1 - y)),) * Z
    wt11 = (((x - x0) * (y - y0)),) * Z

    # ↓ Reading corner pixels and scaling values according to weights above
    norm00 = [*map(mul, pixel(image3d, x0, y0, edge), wt00)]
    norm01 = [*map(mul, pixel(image3d, x0, y1, edge), wt01)]
    norm10 = [*map(mul, pixel(image3d, x1, y0, edge), wt10)]
    norm11 = [*map(mul, pixel(image3d, x1, y1, edge), wt11)]

    # ↓ Adding up pixels by channels
    pixelvalue = [*map(_intaddup, norm00, norm01, norm10, norm11)]

    return pixelvalue


def scale(source_image: list[list[list[int]]], XNEW: int, YNEW: int, edge: int) -> list[list[list[int]]]:
    """Bilinear image rescale, two subsequent 1D passes.

    :param source_image: source image 3D list, coordinate system match Photoshop,
    i.e. origin is top left corner, channels order LA or RGBA from bottom to top;
    :type source_image: list[list[list[int]]]
    :param int XNEW: new image X size, pixels;
    :param int YNEW: new image Y size, pixels;
    :param int edge: edge extrapolation mode:

        - edge=1: repeat edge, like Photoshop;
        - edge=2: wrap around;
        - edge=other: extrapolate with zeroes. Alpha=0 correspond to transparent.
    :return: image, rescaled from ``X``, ``Y`` to ``XNEW``, ``YNEW`` size
    :rtype: list[list[list[int]]]

    """

    # ↓ Determining source image sizes.
    Y = len(source_image)
    X = len(source_image[0])
    Z = len(source_image[0][0])

    # ↓ Function was never FIR-optimized, but @lru_cache() for source rows reading
    #   partially compensate for this.
    #   @lru_cache(maxsize=2) seem to be mostly sufficient.
    @lru_cache(maxsize=4)
    def _pixel_1(x: int, y: int, edge: int) -> list[int]:
        """Local version of pixel(x, y) with hardcoded source list name, good for caching."""
        return pixel(source_image, x, y, edge)

    # ↓ Caching in y-direction works only on tiny images, which are fast to process anyway,
    #   so in most cases caching columns is just a waste of CPU time for dict LRU handling.
    def _pixel_2(x: int, y: int, edge: int) -> list[int]:
        """Local version of pixel(x, y) with hardcoded source list name."""
        return pixel(intermediate_image, x, y, edge)

    def _xlin(x: float, y: int, edge: int) -> list[int]:
        """Returns x-linearly interpolated pixel x, y."""

        def _intaddup(a, b):
            return int(a + b)

        if x >= 0:
            x0 = int(x)
        else:
            x0 = int(x) - 1
        x1 = int(x) + 1

        if x == x0:
            return _pixel_1(x0, y, edge)

        w0 = x1 - x
        w1 = x - x0
        wt0 = ((w0),) * Z
        wt1 = ((w1),) * Z
        px0 = _pixel_1(x0, y, edge)
        px1 = _pixel_1(x1, y, edge)
        norm0 = [*map(mul, px0, wt0)]
        norm1 = [*map(mul, px1, wt1)]

        pixelvalue = [*map(_intaddup, norm0, norm1)]

        return pixelvalue

    def _ylin(x: int, y: float, edge: int) -> list[int]:
        """Returns y-linearly interpolated pixel x, y."""

        def _intaddup(a, b):
            return int(a + b)

        if y >= 0:
            y0 = int(y)
        else:
            y0 = int(y) - 1
        y1 = int(y) + 1

        if y == y0:
            return _pixel_2(x, y0, edge)

        w0 = y1 - y
        w1 = y - y0
        wt0 = ((w0),) * Z
        wt1 = ((w1),) * Z
        px0 = _pixel_2(x, y0, edge)
        px1 = _pixel_2(x, y1, edge)
        norm0 = [*map(mul, px0, wt0)]
        norm1 = [*map(mul, px1, wt1)]

        pixelvalue = [*map(_intaddup, norm0, norm1)]

        return pixelvalue

    # ↓ Two-pass rescaling
    x_resize = (X - 1) / (XNEW - 1)
    y_resize = (Y - 1) / (YNEW - 1)

    if XNEW == X:
        intermediate_image = source_image  # if no rescaling occurs along X
    else:
        intermediate_image = [[_xlin(x_resize * x, y, edge) for x in range(XNEW)] for y in range(Y)]

    if YNEW == Y:
        return intermediate_image  # if no rescaling occurs along Y
    result_image = [[_ylin(x, y_resize * y, edge) for x in range(XNEW)] for y in range(YNEW)]
    # print(_pixel_1.cache_info())

    return result_image


# ↓ Dummy stub for standalone execution attempt
if __name__ == '__main__':
    print('Module to be imported, not run as standalone.')
