"""Image rescaling using bilinear or barycentric interpolation.

Usage
-----

::

    result_image = rescale(source_image, XNEW, YNEW, edge, method)

where

- ``source_image``: source image 3D nested list; coordinate system match Photoshop,
i.e. origin is top left corner, channels order is LA or RGBA from 0 to top;
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

**imin** Git repositories: `@Github`_, `@Gitflic`_.

.. _@Github: https://github.com/Dnyarri/imin

.. _@Gitflic: https://gitflic.ru/project/dnyarri/imin

"""

__author__ = 'Ilya Razmanov'
__copyright__ = '(c) 2024-2026 Ilya Razmanov'
__credits__ = 'Ilya Razmanov'
__license__ = 'unlicense'
__version__ = '26.2.1.9'
__maintainer__ = 'Ilya Razmanov'
__email__ = 'ilyarazmanov@gmail.com'
__status__ = 'Development'

from functools import lru_cache
from operator import mul


# ↓ Pixel reading (local function), nearest neighbour interpolation,
#   configurable edge modes
def _src(source_image: list[list[list[int]]], x: int | float, y: int | float, edge: int | str = 'repeat') -> list[int]:
    """Getting whole pixel from image list, nearest neighbour interpolation,
    returns list[channel] for pixel(x, y)."""

    # ↓ Determining source image sizes.
    Y = len(source_image)
    X = len(source_image[0])
    Z = len(source_image[0][0])

    if edge == 1 or edge == 'repeat':
        # ↓ Repeat edge.
        cx = min(X - 1, max(0, int(x)))
        cy = min(Y - 1, max(0, int(y)))
        pixelvalue = source_image[cy][cx]
    elif edge == 2 or edge == 'wrap':
        # ↓ Wrap around.
        cx = int(x) % X
        cy = int(y) % Y
        pixelvalue = source_image[cy][cx]
    else:
        # ↓ Zeroes.
        if x < 0 or y < 0 or x > X - 1 or y > Y - 1:
            pixelvalue = [0] * Z
        else:
            pixelvalue = source_image[int(y)][int(x)]

    return pixelvalue


# ↓ Two pass rescaling, bilinear interpolation, configurable edge modes
def bilinear(source_image: list[list[list[int]]], XNEW: int, YNEW: int, edge: int | str = 'repeat') -> list[list[list[int]]]:
    """Bilinear image rescale, two subsequent 1D passes.

    :param source_image: source image 3D list, coordinate system match Photoshop,
    i.e. origin is top left corner, channels order LA or RGBA from bottom to top;
    :type source_image: list[list[list[int]]]
    :param int XNEW: ``result_image`` width, pixels;
    :param int YNEW: ``result_image`` height, pixels;
    :param int | str edge: edge extrapolation mode:

        - ``edge=1`` or ``edge='repeat'``: repeat edge, like Photoshop;
        - ``edge=2`` or ``edge='wrap'``: wrap around;
        - ``edge=``other: extrapolate with zeroes. Alpha=0 correspond to transparent.
    :return: image, rescaled from ``X``, ``Y`` to ``XNEW``, ``YNEW`` size
    :rtype: list[list[list[int]]]

    """

    # ↓ Determining source image sizes.
    Y = len(source_image)
    X = len(source_image[0])
    Z = len(source_image[0][0])

    # ↓ Function was never FIR-optimized, but @lru_cache
    #   for source rows reading partially compensate for this.
    @lru_cache(maxsize=4)
    def _pixel_1(x: int, y: int, edge: int | str) -> list[int]:
        """Local version of _src(x, y) with hardcoded source list name, good for caching."""
        return _src(source_image, x, y, edge)

    # ↓ Caching in y-direction works poorly since comprehension works in x-direction,
    #   therefore no caching used.
    def _pixel_2(x: int, y: int, edge: int | str) -> list[int]:
        """Local version of _src(x, y) with hardcoded source list name."""
        return _src(intermediate_image, x, y, edge)

    def _xlin(x: float, y: int, edge: int | str) -> list[int]:
        """Returns x-linearly interpolated pixel(x, y)."""

        def _intaddup(a, b):
            return int(a + b)

        if x >= 0:
            x0 = int(x)
        else:
            x0 = int(x) - 1

        pix0 = _pixel_1(x0, y, edge)
        if x == x0:  # Direct hit. Returns from function!
            return pix0
        x1 = int(x) + 1
        w0 = x1 - x
        w1 = x - x0
        wt0 = (w0,) * Z
        wt1 = (w1,) * Z
        pix1 = _pixel_1(x1, y, edge)
        norm0 = [*map(mul, pix0, wt0)]
        norm1 = [*map(mul, pix1, wt1)]
        pixelvalue = [*map(_intaddup, norm0, norm1)]
        return pixelvalue

    def _ylin(x: int, y: float, edge: int | str) -> list[int]:
        """Returns y-linearly interpolated pixel(x, y)."""

        def _intaddup(a, b):
            return int(a + b)

        if y >= 0:
            y0 = int(y)
        else:
            y0 = int(y) - 1

        pix0 = _pixel_2(x, y0, edge)
        if y == y0:  # Direct hit. Returns from function!
            return pix0
        y1 = int(y) + 1
        w0 = y1 - y
        w1 = y - y0
        wt0 = (w0,) * Z
        wt1 = (w1,) * Z
        pix1 = _pixel_2(x, y1, edge)
        norm0 = [*map(mul, pix0, wt0)]
        norm1 = [*map(mul, pix1, wt1)]
        pixelvalue = [*map(_intaddup, norm0, norm1)]
        return pixelvalue

    # ↓ Resize factor
    x_resize = (X - 1) / (XNEW - 1)
    y_resize = (Y - 1) / (YNEW - 1)

    # ↓ Two-pass rescaling
    if XNEW == X:  # if no rescaling occurs along X
        intermediate_image = source_image
    else:
        intermediate_image = [[_xlin(x_resize * x, y, edge) for x in range(XNEW)] for y in range(Y)]

    if YNEW == Y:  # if no rescaling occurs along Y
        return intermediate_image
    result_image = [[_ylin(x, y_resize * y, edge) for x in range(XNEW)] for y in range(YNEW)]
    # print(_pixel_1.cache_info())

    """
    # ↓ Single pass rescaling.
    #   Included here only for routine retesting of pixel() from __init__.py.
    from imin import pixel
    result_image = [[pixel(source_image, x_resize * x, y_resize * y, edge='repeat', method='bilinear') for x in range(XNEW)] for y in range(YNEW)]
    """

    return result_image


# ↓ Singe pass rescaling, barycentric interpolation, configurable edge modes
def barycentric(source_image: list[list[list[int]]], XNEW: int, YNEW: int, edge: int | str = 'repeat') -> list[list[list[int]]]:
    """Barycentric image rescale.

    :param source_image: source image 3D list, coordinate system match Photoshop,
    i.e. origin is top left corner, channels order LA or RGBA from bottom to top;
    :type source_image: list[list[list[int]]]
    :param int XNEW: ``result_image`` width, pixels;
    :param int YNEW: ``result_image`` height, pixels;
    :param int | str edge: edge extrapolation mode:

        - ``edge=1`` or ``edge='repeat'``: repeat edge, like Photoshop;
        - ``edge=2`` or ``edge='wrap'``: wrap around;
        - ``edge=``other: extrapolate with zeroes. Alpha=0 correspond to transparent.
    :return: image, rescaled from ``X``, ``Y`` to ``XNEW``, ``YNEW`` size
    :rtype: list[list[list[int]]]

    """

    # ↓ Determining source image sizes.
    Y = len(source_image)
    X = len(source_image[0])
    Z = len(source_image[0][0])
    Z_COLOR = Z if Z == 1 or Z == 3 else min(Z - 1, 3)

    # ↓ Function was never FIR-optimized, but @lru_cache
    #   for source rows reading partially compensate for this.
    #   Effects starts at @lru_cache(maxsize=4), and seem to stabilize after maxsize=8.
    #   @lru_cache(maxsize=None) is a tiny yet statistically significant bit faster
    #   but  raise concerns regarding cache size for large images.
    #   On the Toad's behest and volution, maxsize was set
    #   to 8 for images bigger than 256 * 256 px, and None otherwise.
    cache_size = 8 if X * Y > 256 * 256 else None

    @lru_cache(maxsize=cache_size)
    def _pixel(x: int, y: int, edge: int | str) -> list[int]:
        """Local version of _src(x, y) with hardcoded source list name, good for caching."""
        return _src(source_image, x, y, edge)

    def _baryc(x: float, y: float, edge: int | str) -> list[int]:
        """Local version of baryc(x, y) based on _pixel(x, y). Returns interpolated pixel(x, y)."""

        def _intaddup(a, b, c):
            return int(a + b + c)

        if x >= 0:
            x1 = int(x)
        else:
            x1 = int(x) - 1
        if y >= 0:
            y1 = int(y)
        else:
            y1 = int(y) - 1
        pix1 = _pixel(x1, y1, edge)
        if x == x1 and y == y1:  # Direct hit. Returns from function!
            return pix1
        x2 = x1 + 1
        y2 = y1
        x3 = x2
        y3 = y1 + 1
        x4 = x1
        y4 = y3
        pix2 = _pixel(x2, y2, edge)
        pix3 = _pixel(x3, y3, edge)
        pix4 = _pixel(x4, y4, edge)

        if abs(sum(pix1[:Z_COLOR]) - sum(pix3[:Z_COLOR])) < abs(sum(pix2[:Z_COLOR]) - sum(pix4[:Z_COLOR])):
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
                pixelvalue = [*map(_intaddup, norm1, norm3, norm4)]
                return pixelvalue

            a = x2 - x
            b = y - y1
            c = 1 - (a + b)
            at = (a,) * Z
            bt = (b,) * Z
            ct = (c,) * Z
            norm1 = [*map(mul, pix1, at)]
            norm3 = [*map(mul, pix3, bt)]
            norm2 = [*map(mul, pix2, ct)]
            pixelvalue = [*map(_intaddup, norm1, norm3, norm2)]
            return pixelvalue

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
            pixelvalue = [*map(_intaddup, norm1, norm2, norm4)]
            return pixelvalue

        a = x3 - x
        b = y4 - y
        c = 1 - (a + b)
        at = (a,) * Z
        bt = (b,) * Z
        ct = (c,) * Z
        norm4 = [*map(mul, pix4, at)]
        norm2 = [*map(mul, pix2, bt)]
        norm3 = [*map(mul, pix3, ct)]
        pixelvalue = [*map(_intaddup, norm2, norm3, norm4)]
        return pixelvalue

    # ↓ Resize factor
    x_resize = (X - 1) / (XNEW - 1)
    y_resize = (Y - 1) / (YNEW - 1)

    # ↓ Singe pass rescaling
    result_image = [[_baryc(x_resize * x, y_resize * y, edge) for x in range(XNEW)] for y in range(YNEW)]
    # print(_pixel.cache_info())

    """
    # ↓ Single pass rescaling.
    #   Included here only for routine retesting of pixel() from __init__.py.
    from imin import pixel
    result_image = [[pixel(source_image, x_resize * x, y_resize * y, edge='repeat', method='barycentric') for x in range(XNEW)] for y in range(YNEW)]
    """

    return result_image


# ↓ Image rescaling, configurable interpolation, configurable edge modes
def rescale(source_image: list[list[list[int]]], XNEW: int, YNEW: int, edge: int | str = 'repeat', method: int | str = 'bilinear') -> list[list[list[int]]]:
    """Image rescaling, using bilinear or barycentric interpolation depending on ``method``.

    :param source_image: source image 3D list, coordinate system match Photoshop,
    i.e. origin is top left corner, channels order is LA or RGBA from bottom to top;
    :type source_image: list[list[list[int]]]
    :param int XNEW: ``result_image`` width, pixels;
    :param int YNEW: ``result_image`` height, pixels;
    :param int | str edge: edge extrapolation mode:

        - ``edge=1`` or ``edge='repeat'``: repeat edge, like Photoshop;
        - ``edge=2`` or ``edge='wrap'``: wrap around;
        - ``edge=``other: extrapolate with zeroes. Alpha=0 correspond to transparent.
    :param int | str method: interpolation method

        - ``method=2`` or ``method='barycentric'``: barycentric interpolation;
        - ``method=1`` or ``method='bilinear'``: bilinear interpolation;
    :return: image, rescaled from ``X``, ``Y`` to ``XNEW``, ``YNEW`` size
    :rtype: list[list[list[int]]]

    """

    if method == 1 or method == 'bilinear':
        return bilinear(source_image, XNEW, YNEW, edge=edge)
    elif method == 2 or method == 'barycentric':
        return barycentric(source_image, XNEW, YNEW, edge=edge)
    else:
        raise ValueError('Allowed methods are: "bilinear" (1), "barycentric" (2)')
