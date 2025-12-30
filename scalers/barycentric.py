#!/usr/bin/env python3

"""Barycentric image interpolation and rescaling."""

__author__ = 'Ilya Razmanov'
__copyright__ = '(c) 2025 Ilya Razmanov'
__credits__ = 'Ilya Razmanov'
__license__ = 'unlicense'
__version__ = '25.12.14.14'
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


def baryc(image3d: list[list[list[int]]], x: float, y: float, edge: int) -> list[int]:
    """Returns barycentrically interpolated pixel(x, y).

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

    def _intaddup(a, b, c):
        return int(a + b + c)

    # ↓ Determining source image sizes.
    #   Y = len(image3d)
    #   X = len(image3d[0])
    Z = len(image3d[0][0])

    # ↓ Number of color channels, alpha excluded.
    Z_COLOR = Z if Z == 1 or Z == 3 else min(Z - 1, 3)

    """ Square corners are enumerated according to Soviet Army «snail» scheme
        ┌───┬───┐
        │ 1 │ 2 │
        ├───┼───┤
        │ 4 │ 3 │
        └───┴───┘
        and square divided onto two triangles by either 1-3 [╲] or 2-4 [╱] diagonal
        depending on what difference is bigger (i.e. on directional local contrast). 

        Each triangle is right-angled and takes 0.5 of 1×1 length unit square area
        (i.e. 2×2 pixel number square), that greatly simplifies calculation.

    NOTE: Corners coordinates are calculated taking into account that
    for negative x and y values
        int(x) > x
            and
        int(y) > y
        correspondingly. """

    if x >= 0:
        x1 = int(x)
    else:
        x1 = int(x) - 1
    if y >= 0:
        y1 = int(y)
    else:
        y1 = int(y) - 1
    x2 = x1 + 1
    y2 = y1
    x3 = x2
    y3 = y1 + 1
    x4 = x1
    y4 = y3

    # ↓ Corners pixels
    p1 = pixel(image3d, x1, y1, edge)
    # ↓ In case of direct hit, no interpolation required
    if x == x1 and y == y1:
        return p1
    # ↓ When direct hit misses, interpolation goes on
    p2 = pixel(image3d, x2, y2, edge)
    p3 = pixel(image3d, x3, y3, edge)
    p4 = pixel(image3d, x4, y4, edge)

    """ Now going to choose the diagonal for 2×2 pixel square folding based on
        comparing differences between pixels in 🡦 and 🡧 directions.
        Currently total sum of channels (excluding alpha) is used for comparison.
        The choice is questionable, but pro et contra may be given for any. """

    if abs(sum(p1[:Z_COLOR]) - sum(p3[:Z_COLOR])) < abs(sum(p2[:Z_COLOR]) - sum(p4[:Z_COLOR])):
        # ↓ ╲ diagonal
        if (x - x1) < (y - y1):
            # ↓ ◣ 1-3-4 triangle
            #   Doubled subtriangle area (i.e. base subrectangle area) is calculated,
            #   since it's normalized to unit square already.
            a = x - x1
            b = y4 - y
            c = 1 - (a + b)

            norm3 = [*map(mul, p3, (a,) * Z)]
            norm1 = [*map(mul, p1, (b,) * Z)]
            norm4 = [*map(mul, p4, (c,) * Z)]

            pixelvalue = [*map(_intaddup, norm1, norm3, norm4)]

            return pixelvalue

        # ↓ ◥ 1-2-3 triangle
        a = x2 - x
        b = y - y1
        c = 1 - (a + b)

        norm1 = [*map(mul, p1, (a,) * Z)]
        norm3 = [*map(mul, p3, (b,) * Z)]
        norm2 = [*map(mul, p2, (c,) * Z)]

        pixelvalue = [*map(_intaddup, norm1, norm3, norm2)]

        return pixelvalue

    # ↓ ╱ diagonal
    if (x - x1) < (y3 - y):
        # ↓ ◤ 1-2-4 triangle
        a = x - x1
        b = y - y1
        c = 1 - (a + b)

        norm2 = [*map(mul, p2, (a,) * Z)]
        norm4 = [*map(mul, p4, (b,) * Z)]
        norm1 = [*map(mul, p1, (c,) * Z)]

        pixelvalue = [*map(_intaddup, norm1, norm2, norm4)]

        return pixelvalue

    # ↓ ◢ 2-3-4 triangle
    a = x3 - x
    b = y4 - y
    c = 1 - (a + b)

    norm4 = [*map(mul, p4, (a,) * Z)]
    norm2 = [*map(mul, p2, (b,) * Z)]
    norm3 = [*map(mul, p3, (c,) * Z)]

    pixelvalue = [*map(_intaddup, norm2, norm3, norm4)]

    return pixelvalue


def scale(source_image: list[list[list[int]]], XNEW: int, YNEW: int, edge: int) -> list[list[list[int]]]:
    """Barycentric image rescale.

    :param source_image: source image 3D list, coordinate system match Photoshop,
    i.e. origin is top left corner, channels order LA or RGBA from bottom to top;
    :type source_image: list[list[list[int]]]
    :param int XNEW: new image X size, pixels;
    :param int YNEW: new image Y size, pixels;
    :param int edge: edge extrapolation mode:

        - edge=1: repeat edge, like Photoshop;
        - edge=2: wrap around;
        - edge=other: extrapolate with zeroes. Fortunately alpha=0 correspond to transparent.
    :return: image, rescaled from ``X``, ``Y`` to ``XNEW``, ``YNEW`` size
    :rtype: list[list[list[int]]]

    """

    # ↓ Determining source image sizes.
    Y = len(source_image)
    X = len(source_image[0])
    Z = len(source_image[0][0])

    # ↓ Function was never FIR-optimized, but @lru_cache() partially compensate for this.
    #   Effects starts at @lru_cache(maxsize=4), and seem to stabilize after maxsize=8.
    #   @lru_cache(maxsize=None) is more efficient but raise concerns
    #   regarding cache size for large images.
    #   As a result, on the Toad's behest and volution, maxsize was set
    #   to 8 for images bigger than 256 * 256 px, and None otherwise.
    cache_size = 8 if X * Y > 256 * 256 else None

    @lru_cache(maxsize=cache_size)
    def _pixel(x: int, y: int, edge: int) -> list[int]:
        """Local version of pixel(x, y) with hardcoded source list name, good for caching."""

        return pixel(source_image, x, y, edge)

    def _baryc(x: float, y: float, edge: int) -> list[int]:
        """Local version of baryc(x, y) based on _pixel(x, y). Returns interpolated pixel x, y."""

        def _intaddup(a, b, c):
            return int(a + b + c)

        Z_COLOR = Z if Z == 1 or Z == 3 else min(Z - 1, 3)

        if x >= 0:
            x1 = int(x)
        else:
            x1 = int(x) - 1
        if y >= 0:
            y1 = int(y)
        else:
            y1 = int(y) - 1
        x2 = x1 + 1
        y2 = y1
        x3 = x2
        y3 = y1 + 1
        x4 = x1
        y4 = y3
        p1 = _pixel(x1, y1, edge)
        if x == x1 and y == y1:
            return p1
        p2 = _pixel(x2, y2, edge)
        p3 = _pixel(x3, y3, edge)
        p4 = _pixel(x4, y4, edge)

        if abs(sum(p1[:Z_COLOR]) - sum(p3[:Z_COLOR])) < abs(sum(p2[:Z_COLOR]) - sum(p4[:Z_COLOR])):
            if (x - x1) < (y - y1):
                a = x - x1
                b = y4 - y
                c = 1 - (a + b)
                norm3 = [*map(mul, p3, (a,) * Z)]
                norm1 = [*map(mul, p1, (b,) * Z)]
                norm4 = [*map(mul, p4, (c,) * Z)]
                pixelvalue = [*map(_intaddup, norm1, norm3, norm4)]
                return pixelvalue

            a = x2 - x
            b = y - y1
            c = 1 - (a + b)
            norm1 = [*map(mul, p1, (a,) * Z)]
            norm3 = [*map(mul, p3, (b,) * Z)]
            norm2 = [*map(mul, p2, (c,) * Z)]
            pixelvalue = [*map(_intaddup, norm1, norm3, norm2)]
            return pixelvalue

        if (x - x1) < (y3 - y):
            a = x - x1
            b = y - y1
            c = 1 - (a + b)
            norm2 = [*map(mul, p2, (a,) * Z)]
            norm4 = [*map(mul, p4, (b,) * Z)]
            norm1 = [*map(mul, p1, (c,) * Z)]
            pixelvalue = [*map(_intaddup, norm1, norm2, norm4)]
            return pixelvalue

        a = x3 - x
        b = y4 - y
        c = 1 - (a + b)
        norm4 = [*map(mul, p4, (a,) * Z)]
        norm2 = [*map(mul, p2, (b,) * Z)]
        norm3 = [*map(mul, p3, (c,) * Z)]
        pixelvalue = [*map(_intaddup, norm2, norm3, norm4)]
        return pixelvalue

    # _baryc end

    # ↓ Singe pass rescaling
    x_resize = (X - 1) / (XNEW - 1)
    y_resize = (Y - 1) / (YNEW - 1)

    result_image = [[_baryc(x_resize * x, y_resize * y, edge) for x in range(XNEW)] for y in range(YNEW)]
    # print(_pixel.cache_info())

    return result_image


# ↓ Dummy stub for standalone execution attempt
if __name__ == '__main__':
    print('Module to be imported, not run as standalone.')
