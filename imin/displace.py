"""Generalized image pixels displacement using bilinear or barycentric interpolation.

Usage
-----

::

    result_image = displace(source_image, fx, fy, XNEW, YNEW, edge, method)

where

- ``source_image``: source image 3D nested list; coordinate system match Photoshop,
i.e. origin is top left corner, channels order is LA or RGBA from 0 to top;
- ``fx``: actual x coordinate to read as a function of (x, y) requested;
- ``fy``: actual y coordinate to read as a function of (x, y) requested;
- ``XNEW``: ``result_image`` width, pixels;
- ``YNEW``: ``result_image`` height, pixels;
- ``edge``: edge extrapolation mode:
    - ``edge=1`` or ``edge='repeat'``: repeat edge, like Photoshop;
    - ``edge=2`` or ``edge='wrap'``: wrap around;
    - ``edge=``other: extrapolate with zeroes. Alpha=0 means transparent.

- ``method``: image interpolation method:
    - ``method=1`` or ``method='bilinear'``: bilinear interpolation;
    - ``method=2`` or ``method='barycentric'``: barycentric interpolation.

Return ``result_image`` 3D list of the same structure as ``source_image``.

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
__copyright__ = '(c) 2024-2026 Ilya Razmanov'
__credits__ = 'Ilya Razmanov'
__license__ = 'unlicense'
__version__ = '26.8.2.16'
__maintainer__ = 'Ilya Razmanov'
__email__ = 'ilyarazmanov@gmail.com'
__status__ = 'Development'
__all__ = ['displace']

from functools import lru_cache
from operator import mul


# ↓ Pixel reading (local function), nearest neighbour interpolation,
#   configurable edge modes
def _src(source_image: list[list[list[int]]], x: float, y: float, edge: int | str = 'repeat', X: int = 1, Y: int = 1, Z: int = 1) -> list[int]:
    """Reading pixel(x, y) list from image nested list, nearest neighbour interpolation.
    
    .. warning:: Unlike global src(source_image,x,y,edge), **REQUIRES X, Y, Z**
        to avoid recalculating it for every pixel!
    """

    Z_COLOR = Z if Z == 1 or Z == 3 else min(Z - 1, 3)  # Number of color channels, alpha excluded.

    if edge == 1 or edge == 'repeat':
        # ↓ Repeat edge.
        cx = min(X - 1, max(0, int(x)))
        cy = min(Y - 1, max(0, int(y)))
        pixelvalue = source_image[cy][cx]
        return pixelvalue
    if edge == 2 or edge == 'wrap':
        # ↓ Wrap around.
        cx = int(x) % X
        cy = int(y) % Y
        pixelvalue = source_image[cy][cx]
        return pixelvalue
    else:
        # ↓ Zeroes.
        if x < 0 or y < 0 or x > X - 1 or y > Y - 1:  # Edge processing.
            if Z == 1 or Z == 3:
                pixelvalue = [0] * Z
            else:
                cx = min(X - 1, max(0, int(x)))
                cy = min(Y - 1, max(0, int(y)))
                pixelvalue = [*source_image[cy][cx][:Z_COLOR], 0]
        else:  # Non-edge processing.
            pixelvalue = source_image[int(y)][int(x)]
        return pixelvalue


# ↓ Singe pass displacement, bilinear interpolation, configurable edge modes
def bilinear(source_image: list[list[list[int]]], fx: callable, fy: callable, XNEW: int, YNEW: int, edge: int | str) -> list[list[list[int]]]:
    """Bilinear image displacement according to ``fx`` and ``fy`` functions.

    :param source_image: source image 3D list, coordinate system match Photoshop,
        i.e. origin is top left corner, channels order is
        LA or RGBA from bottom to top;
    :type source_image: list[list[list[int]]]
    :param fx: actual x coordinate to read as a function of (x, y) requested;
    :type fx: function[float, float] -> float
    :param fy: actual y coordinate to read as a function of (x, y) requested;
    :type fy: function[float, float] -> float
    :param int XNEW: ``result_image`` width, pixels;
    :param int YNEW: ``result_image`` height, pixels;
    :param int | str edge: edge extrapolation mode:

        - ``edge=1`` or ``edge='repeat'``: repeat edge, like Photoshop;
        - ``edge=2`` or ``edge='wrap'``: wrap around;
        - ``edge=``other: extrapolate with zeroes.
          Alpha=0 correspond to transparent.
    :return: image, distorted according to ``fx``, ``fy`` rules.
    :rtype: list[list[list[int]]]

    """

    # ↓ Determining source image sizes.
    Y, X, Z = (len(source_image), len(source_image[0]), len(source_image[0][0]))

    # ↓ Function was never FIR-optimized, but @lru_cache
    #   for source rows reading partially compensate for this.
    #   Unfortunately, both optimal cache size and actual effect
    #   on arbitrary displacement depend on exact displacement
    #   and therefore are unpredictable.
    @lru_cache
    def _pixel(x: int, y: int, edge: int | str, X: int, Y: int, Z: int) -> list[int]:
        """Local version of _src(x, y) with hardcoded source list name, good for caching."""
        return _src(source_image, x, y, edge, X, Y, Z)

    def _blin(x: float, y: float, edge: int | str, X: int, Y: int, Z: int) -> list[int]:
        """Local version of blin(x, y) based on _pixel(x, y). Returns interpolated pixel(x, y)."""

        def _intaddup_4(a, b, c, d):
            return int(a + b + c + d)

        if x >= 0:
            x0 = int(x)
        else:
            x0 = int(x) - 1
        if y >= 0:
            y0 = int(y)
        else:
            y0 = int(y) - 1

        pix00 = _pixel(x0, y0, edge, X, Y, Z)
        if x == x0 and y == y0:  # Direct hit. Returns from function!
            return pix00
        x1 = x0 + 1
        y1 = y0 + 1
        wt00 = (((x1 - x) * (y1 - y)),) * Z
        wt01 = (((x1 - x) * (y - y0)),) * Z
        wt10 = (((x - x0) * (y1 - y)),) * Z
        wt11 = (((x - x0) * (y - y0)),) * Z
        norm00 = [*map(mul, pix00, wt00)]
        norm01 = [*map(mul, _pixel(x0, y1, edge, X, Y, Z), wt01)]
        norm10 = [*map(mul, _pixel(x1, y0, edge, X, Y, Z), wt10)]
        norm11 = [*map(mul, _pixel(x1, y1, edge, X, Y, Z), wt11)]
        pixelvalue = [*map(_intaddup_4, norm00, norm01, norm10, norm11)]
        return pixelvalue

    # ↓ Singe pass displacement
    result_image = [[_blin(fx(x, y), fy(x, y), edge, X, Y, Z) for x in range(XNEW)] for y in range(YNEW)]
    # print(_pixel.cache_info())

    return result_image


# ↓ Singe pass displacement, barycentric interpolation, configurable edge modes
def barycentric(source_image: list[list[list[int]]], fx: callable, fy: callable, XNEW: int, YNEW: int, edge: int | str) -> list[list[list[int]]]:
    """Barycentric image displacement according to ``fx`` and ``fy`` functions.

    :param source_image: source image 3D list, coordinate system match Photoshop,
        i.e. origin is top left corner, channels order is
        LA or RGBA from bottom to top;
    :type source_image: list[list[list[int]]]
    :param fx: actual x coordinate to read as a function of (x, y) requested;
    :type fx: function[float, float] -> float
    :param fy: actual y coordinate to read as a function of (x, y) requested;
    :type fy: function[float, float] -> float
    :param int XNEW: ``result_image`` width, pixels;
    :param int YNEW: ``result_image`` height, pixels;
    :param int | str edge: edge extrapolation mode:

        - ``edge=1`` or ``edge='repeat'``: repeat edge, like Photoshop;
        - ``edge=2`` or ``edge='wrap'``: wrap around;
        - ``edge=``other: extrapolate with zeroes.
          Alpha=0 correspond to transparent.
    :return: image, distorted according to ``fx``, ``fy`` rules.
    :rtype: list[list[list[int]]]

    """

    # ↓ Determining source image sizes.
    Y, X, Z = (len(source_image), len(source_image[0]), len(source_image[0][0]))
    Z_COLOR = Z if Z == 1 or Z == 3 else min(Z - 1, 3)

    # ↓ Function was never FIR-optimized, but @lru_cache
    #   for source rows reading partially compensate for this.
    #   Unfortunately, both optimal cache size and actual effect
    #   on arbitrary displacement depend on exact displacement
    #   and therefore are unpredictable.
    @lru_cache
    def _pixel(x: int, y: int, edge: int | str, X: int, Y: int, Z: int) -> list[int]:
        """Local version of _src(x, y) with hardcoded source list name, good for caching."""
        return _src(source_image, x, y, edge, X, Y, Z)

    def _baryc(x: float, y: float, edge: int | str, X: int, Y: int, Z: int) -> list[int]:
        """Local version of baryc(x, y) based on _pixel(x, y)."""

        def _intaddup_3(a, b, c):
            return int(a + b + c)

        if x >= 0:
            x1 = int(x)
        else:
            x1 = int(x) - 1
        if y >= 0:
            y1 = int(y)
        else:
            y1 = int(y) - 1
        pix1 = _pixel(x1, y1, edge, X, Y, Z)
        if x == x1 and y == y1:  # Direct hit. Returns from function!
            return pix1
        x2 = x1 + 1
        y2 = y1
        x3 = x2
        y3 = y1 + 1
        x4 = x1
        y4 = y3
        pix2 = _pixel(x2, y2, edge, X, Y, Z)
        pix3 = _pixel(x3, y3, edge, X, Y, Z)
        pix4 = _pixel(x4, y4, edge, X, Y, Z)

        diff13 = abs(sum(pix1[:Z_COLOR]) - sum(pix3[:Z_COLOR]))
        diff24 = abs(sum(pix2[:Z_COLOR]) - sum(pix4[:Z_COLOR]))

        if diff13 < diff24:  # ╲ diagonal
            if (x - x1) < (y - y1):
                a = x - x1
                b = y4 - y
                c = 1 - (a + b)
                at = (a,) * Z
                bt = (b,) * Z
                ct = (c,) * Z
                norm3 = [*map(mul, pix3, at)]
                norm1 = [*map(mul, pix1, bt)]
                norm4 = [*map(mul, pix4, ct)]
                pixelvalue = [*map(_intaddup_3, norm1, norm3, norm4)]
                return pixelvalue

            if (x - x1) > (y - y1):
                a = x2 - x
                b = y - y1
                c = 1 - (a + b)
                at = (a,) * Z
                bt = (b,) * Z
                ct = (c,) * Z
                norm1 = [*map(mul, pix1, at)]
                norm3 = [*map(mul, pix3, bt)]
                norm2 = [*map(mul, pix2, ct)]
                pixelvalue = [*map(_intaddup_3, norm1, norm3, norm2)]
                return pixelvalue

        if diff13 > diff24:  # ╱ diagonal
            if (x - x1) < (y3 - y):
                a = x - x1
                b = y - y1
                c = 1 - (a + b)
                at = (a,) * Z
                bt = (b,) * Z
                ct = (c,) * Z
                norm2 = [*map(mul, pix2, at)]
                norm4 = [*map(mul, pix4, bt)]
                norm1 = [*map(mul, pix1, ct)]
                pixelvalue = [*map(_intaddup_3, norm1, norm2, norm4)]
                return pixelvalue

            if (x - x1) > (y3 - y):
                a = x3 - x
                b = y4 - y
                c = 1 - (a + b)
                at = (a,) * Z
                bt = (b,) * Z
                ct = (c,) * Z
                norm4 = [*map(mul, pix4, at)]
                norm2 = [*map(mul, pix2, bt)]
                norm3 = [*map(mul, pix3, ct)]
                pixelvalue = [*map(_intaddup_3, norm2, norm3, norm4)]
                return pixelvalue

        # ↓ If no diagonal chosen, bilinear interpolation kicks in
        def _intaddup_4(a, b, c, d):
            return int(a + b + c + d)

        w1 = (x3 - x) * (y3 - y)
        w2 = (x - x4) * (y4 - y)
        w3 = (x - x1) * (y - y1)
        w4 = (x2 - x) * (y - y2)
        wt1 = (w1,) * Z
        wt2 = (w2,) * Z
        wt3 = (w3,) * Z
        wt4 = (w4,) * Z
        norm1 = [*map(mul, pix1, wt1)]
        norm2 = [*map(mul, pix2, wt2)]
        norm3 = [*map(mul, pix3, wt3)]
        norm4 = [*map(mul, pix4, wt4)]
        pixelvalue = [*map(_intaddup_4, norm1, norm4, norm2, norm3)]
        return pixelvalue

    # ↓ Singe pass displacement
    result_image = [[_baryc(fx(x, y), fy(x, y), edge, X, Y, Z) for x in range(XNEW)] for y in range(YNEW)]
    # print(_pixel.cache_info())

    return result_image


# ↓ Image displacement, configurable interpolation, configurable edge modes
def displace(source_image: list[list[list[int]]], fx: callable, fy: callable, XNEW: int, YNEW: int, edge: int | str = 0, method: int | str = 'bilinear') -> list[list[list[int]]]:
    """Image displacement according to ``fx`` and ``fy`` functions, using bilinear or barycentric interpolation depending on ``method`` switch.

    :param source_image: source image 3D nested list,
        coordinate system match Photoshop, i.e. origin is top left corner,
        channels order is LA or RGBA from bottom to top;
    :type source_image: list[list[list[int]]]
    :param fx: actual x coordinate to read as a function of (x, y) requested;
    :type fx: callable[float, float]
    :param fy: actual y coordinate to read as a function of (x, y) requested;
    :type fy: callable[float, float]
    :param int XNEW: ``result_image`` width, pixels;
    :param int YNEW: ``result_image`` height, pixels;
    :param int | str edge: edge extrapolation mode:

        - ``edge=1`` or ``edge='repeat'``: repeat edge, like Photoshop;
        - ``edge=2`` or ``edge='wrap'``: wrap around;
        - ``edge=``other: extrapolate with zeroes.
          Alpha=0 correspond to transparent.
    :param int | str method: interpolation method

        - ``method=2`` or ``method='barycentric'``: barycentric interpolation;
        - ``method=1`` or ``method='bilinear'``: bilinear interpolation;
    :return: image, distorted according to ``fx``, ``fy`` rules.
    :rtype: list[list[list[int]]]

    """

    if method == 1 or method == 'bilinear':
        return bilinear(source_image, fx, fy, XNEW, YNEW, edge=edge)
    elif method == 2 or method == 'barycentric':
        return barycentric(source_image, fx, fy, XNEW, YNEW, edge=edge)
    else:
        raise ValueError('Allowed methods are: "bilinear" (1), "barycentric" (2)')
