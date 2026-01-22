"""Generalized image displacement with barycentric or bilinear interpolation.

Usage
-----

::

    result_image = displace(source_image, fx, fy, XNEW, YNEW, edge, method)

where

- ``source_image``: source image 3D nested list; coordinate system match Photoshop,
i.e. origin is top left corner, channels order is LA or RGBA from 0 to top;
- ``fx``: actual x coordinate to read as a function of formal x, y counters;
- ``fy``: actual y coordinate to read as a function of formal x, y counters;
- ``XNEW``: new image X size, pixels;
- ``YNEW``: new image Y size, pixels;
- ``edge``: edge extrapolation mode:
    - ``edge=1`` or ``edge='repeat'``: repeat edge, like Photoshop;
    - ``edge=2`` or ``edge='wrap'``: wrap around;
    - ``edge=``other: extrapolate with zeroes;
- ``method``: image interpolation method:
    - ``method=1`` or ``method='bilinear'``: bilinear interpolation;
    - ``method=2`` or ``method='barycentric'``: barycentric interpolation.

Return ``result_image`` 3D list of the same structure as ``source_image``.

----
**Main site**: `The Toad's Slimy Mudhole`_

.. _The Toad's Slimy Mudhole: https://dnyarri.github.io/

**imin** Git repositories: `@Github`_, `@Gitflic`_.

.. _@Github: https://github.com/Dnyarri/imin

.. _@Gitflic: https://gitflic.ru/project/dnyarri/imin

"""

__author__ = 'Ilya Razmanov'
__copyright__ = '(c) 2024-2026 Ilya Razmanov'
__credits__ = 'Ilya Razmanov'
__license__ = 'unlicense'
__version__ = '26.1.21.7'
__maintainer__ = 'Ilya Razmanov'
__email__ = 'ilyarazmanov@gmail.com'
__status__ = 'Development'

from functools import lru_cache
from operator import mul


# ↓ Pixel reading, local version, different edge modes, nearest neighbour
def _src(image3d: list[list[list[int]]], x: int | float, y: int | float, edge: int | str = 1) -> list[int]:
    """Getting whole pixel from image list, nearest neighbour interpolation,
    returns list[channel] for pixel(x, y)."""

    # ↓ Determining source image sizes.
    Y = len(image3d)
    X = len(image3d[0])
    Z = len(image3d[0][0])

    if edge == 1 or edge == 'repeat':
        # ↓ Repeat edge.
        cx = min((X - 1), max(0, int(x)))
        cy = min((Y - 1), max(0, int(y)))
        pixelvalue = image3d[cy][cx]
    elif edge == 2 or edge == 'wrap':
        # ↓ Wrap around.
        cx = int(x) % X
        cy = int(y) % Y
        pixelvalue = image3d[cy][cx]
    else:
        # ↓ Zeroes.
        if x < 0 or y < 0 or x > X - 1 or y > Y - 1:
            pixelvalue = [0] * Z
        else:
            pixelvalue = image3d[int(y)][int(x)]

    return pixelvalue


# ↓ Singe pass displacement, bilinear
def bilinear(source_image: list[list[list[int]]], fx, fy, XNEW: int, YNEW: int, edge: int | str, **kwargs) -> list[list[list[int]]]:
    """Bilinear image displacement according to ``fx`` and ``fy`` functions.

    :param source_image: source image 3D list, coordinate system match Photoshop,
    i.e. origin is top left corner, channels order is LA or RGBA from bottom to top;
    :type source_image: list[list[list[int]]]
    :param fx: actual x coordinate to read as a function of formal x, y counters
    :type fx: function
    :param fy: actual y coordinate to read as a function of formal x, y counters
    :type fy: function
    :param int XNEW: new image X size, pixels;
    :param int YNEW: new image Y size, pixels;
    :param int | str edge: edge extrapolation mode:

        - ``edge=1`` or ``edge='repeat'``: repeat edge, like Photoshop;
        - ``edge=2`` or ``edge='wrap'``: wrap around;
        - ``edge=``other: extrapolate with zeroes. Alpha=0 correspond to transparent.
    :return: image, distorted according to ``fx``, ``fy`` rules.
    :rtype: list[list[list[int]]]

    """

    # ↓ Determining source image sizes.
    # Y = len(source_image)
    # X = len(source_image[0])
    Z = len(source_image[0][0])

    # ↓ Function was never FIR-optimized, but @lru_cache for source rows reading
    #   partially compensate for this.
    #   Unfortunately, both optimal cache size and actual effect
    #   on arbitrary displacement are unpredictable.
    @lru_cache
    def _pixel(x: int, y: int, edge: int | str) -> list[int]:
        """Local version of _src(x, y) with hardcoded source list name, good for caching."""

        return _src(source_image, x, y, edge)

    def _blin(x: float, y: float, edge: int | str) -> list[int]:
        """Local version of blin(x, y) based on _pixel(x, y). Returns interpolated pixel x, y."""

        def _intaddup(a, b, c, d):
            return int(a + b + c + d)

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
            return _pixel(x0, y0, edge)
        # ↓ When direct hit misses, interpolation goes on
        x1 = x0 + 1
        y1 = y0 + 1

        # ↓ Distance weights for pixels, packed as tuple for map() below
        wt00 = (((x1 - x) * (y1 - y)),) * Z
        wt01 = (((x1 - x) * (y - y0)),) * Z
        wt10 = (((x - x0) * (y1 - y)),) * Z
        wt11 = (((x - x0) * (y - y0)),) * Z

        # ↓ Reading corner pixels and scaling values according to weights above
        norm00 = [*map(mul, _pixel(x0, y0, edge), wt00)]
        norm01 = [*map(mul, _pixel(x0, y1, edge), wt01)]
        norm10 = [*map(mul, _pixel(x1, y0, edge), wt10)]
        norm11 = [*map(mul, _pixel(x1, y1, edge), wt11)]

        # ↓ Adding up pixels by channels
        pixelvalue = [*map(_intaddup, norm00, norm01, norm10, norm11)]

        return pixelvalue

    # ↓ Singe pass displacement
    result_image = [[_blin(fx(x, y), fy(x, y), edge) for x in range(XNEW)] for y in range(YNEW)]
    # print(_pixel.cache_info())
    return result_image


# ↓ Singe pass displacement, barycentric
def barycentric(source_image: list[list[list[int]]], fx, fy, XNEW: int, YNEW: int, edge: int | str, **kwargs) -> list[list[list[int]]]:
    """Barycentric image displacement according to ``fx`` and ``fy`` functions.

    :param source_image: source image 3D list, coordinate system match Photoshop,
    i.e. origin is top left corner, channels order is LA or RGBA from bottom to top;
    :type source_image: list[list[list[int]]]
    :param fx: actual x coordinate to read as a function of formal x, y counters
    :type fx: function
    :param fy: actual y coordinate to read as a function of formal x, y counters
    :type fy: function
    :param int XNEW: new image X size, pixels;
    :param int YNEW: new image Y size, pixels;
    :param int | str edge: edge extrapolation mode:

        - ``edge=1`` or ``edge='repeat'``: repeat edge, like Photoshop;
        - ``edge=2`` or ``edge='wrap'``: wrap around;
        - ``edge=``other: extrapolate with zeroes. Alpha=0 correspond to transparent.
    :return: image, distorted according to ``fx``, ``fy`` rules.
    :rtype: list[list[list[int]]]

    """

    # ↓ Determining source image sizes.
    # Y = len(source_image)
    # X = len(source_image[0])
    Z = len(source_image[0][0])

    # ↓ Function was never FIR-optimized, but @lru_cache for source rows reading
    #   partially compensate for this.
    #   Unfortunately, both optimal cache size and actual effect
    #   on arbitrary displacement are unpredictable.
    @lru_cache
    def _pixel(x: int, y: int, edge: int | str) -> list[int]:
        """Local version of _src(x, y) with hardcoded source list name, good for caching."""

        return _src(source_image, x, y, edge)

    def _baryc(x: float, y: float, edge: int | str) -> list[int]:
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

    # ↓ Singe pass displacement
    result_image = [[_baryc(fx(x, y), fy(x, y), edge) for x in range(XNEW)] for y in range(YNEW)]
    # print(_pixel.cache_info())

    return result_image


# ↓ Singe pass displacement, general
def displace(source_image: list[list[list[int]]], fx, fy, XNEW: int, YNEW: int, edge: int | str = 0, method: int | str = 1, **kwargs) -> list[list[list[int]]]:
    """Image displacement according to ``fx`` and ``fy`` functions, using bilinear or barycentric interpolation depending on ``method``.

    :param source_image: source image 3D list, coordinate system match Photoshop,
    i.e. origin is top left corner, channels order is LA or RGBA from bottom to top;
    :type source_image: list[list[list[int]]]
    :param fx: actual x coordinate to read as a function of formal x, y counters
    :type fx: function
    :param fy: actual y coordinate to read as a function of formal x, y counters
    :type fy: function
    :param int XNEW: new image X size, pixels;
    :param int YNEW: new image Y size, pixels;
    :param int | str edge: edge extrapolation mode:

        - ``edge=1`` or ``edge='repeat'``: repeat edge, like Photoshop;
        - ``edge=2`` or ``edge='wrap'``: wrap around;
        - ``edge=``other: extrapolate with zeroes. Alpha=0 correspond to transparent.
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
        raise ValueError('Allowed methods are 1 and 2')
