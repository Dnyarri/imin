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
__all__ = ['rescale']

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


# ↓ Two pass rescaling, bilinear interpolation, configurable edge modes
def bilinear(source_image: list[list[list[int]]], XNEW: int, YNEW: int, edge: int | str = 'repeat') -> list[list[list[int]]]:
    """Bilinear image rescale, two subsequent 1D passes.

    :param source_image: source image 3D list, coordinate system match Photoshop,
        i.e. origin is top left corner, channels order is
        LA or RGBA from bottom to top;
    :type source_image: list[list[list[int]]]
    :param int XNEW: ``result_image`` width, pixels;
    :param int YNEW: ``result_image`` height, pixels;
    :param int | str edge: edge extrapolation mode:

        - ``edge=1`` or ``edge='repeat'``: repeat edge, like Photoshop;
        - ``edge=2`` or ``edge='wrap'``: wrap around;
        - ``edge=``other: extrapolate with zeroes.
          Alpha=0 correspond to transparent.
    :return: image, rescaled from ``X``, ``Y`` to ``XNEW``, ``YNEW`` size.
    :rtype: list[list[list[int]]]

    """

    """ ┍━ Pass 1 ━━━━━━━━━━━━━━┑
        │ Horizontal rescaling. │
        ╰───────────────────────╯ """
    # ↓ Determining source image sizes.
    Y, X, Z = (len(source_image), len(source_image[0]), len(source_image[0][0]))

    # ↓ Function was never FIR-optimized, but @lru_cache
    #   for source rows reading partially compensate for this.
    @lru_cache(maxsize=4)
    def _pixel_1(x: int, y: int, edge: int | str, X: int, Y: int, Z: int) -> list[int]:
        """Local version of _src(x, y) with hardcoded source list name, good for caching."""
        return _src(source_image, x, y, edge, X, Y, Z)

    def _xlin(x: float, y: int, edge: int | str) -> list[int]:
        """Returns x-linearly interpolated pixel(x, y)."""

        def _intaddup(a, b):
            return int(a + b)

        if x >= 0:
            x0 = int(x)
        else:
            x0 = int(x) - 1

        pix0 = _pixel_1(x0, y, edge, X, Y, Z)
        if x == x0:  # Direct hit. Returns from function!
            return pix0
        x1 = int(x) + 1
        w0 = x1 - x
        w1 = x - x0
        wt0 = (w0,) * Z
        wt1 = (w1,) * Z
        pix1 = _pixel_1(x1, y, edge, X, Y, Z)
        norm0 = [*map(mul, pix0, wt0)]
        norm1 = [*map(mul, pix1, wt1)]
        pixelvalue = [*map(_intaddup, norm0, norm1)]
        return pixelvalue

    """ ┍━ Pass 2 ━━━━━━━━━━━━┑
        │ Vertical rescaling. │
        ╰─────────────────────╯ """
    # ↓ Determining intermediate image sizes.
    Y2, X2, Z2 = (Y, XNEW, Z)

    # ↓ Caching in y-direction works poorly since comprehension
    #   works in x-direction, therefore no caching used.
    def _pixel_2(x: int, y: int, edge: int | str, X2: int, Y2: int, Z2: int) -> list[int]:
        """Local version of _src(x, y) with hardcoded source list name."""
        return _src(intermediate_image, x, y, edge, X=X2, Y=Y2, Z=Z2)

    def _ylin(x: int, y: float, edge: int | str) -> list[int]:
        """Returns y-linearly interpolated pixel(x, y)."""

        def _intaddup(a, b):
            return int(a + b)

        if y >= 0:
            y0 = int(y)
        else:
            y0 = int(y) - 1

        pix0 = _pixel_2(x, y0, edge, X2, Y2, Z2)
        if y == y0:  # Direct hit. Returns from function!
            return pix0
        y1 = int(y) + 1
        w0 = y1 - y
        w1 = y - y0
        wt0 = (w0,) * Z
        wt1 = (w1,) * Z
        pix1 = _pixel_2(x, y1, edge, X2, Y2, Z2)
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
    # print(f'{_pixel_1.cache_info()=}')

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
        i.e. origin is top left corner, channels order is
        LA or RGBA from bottom to top;
    :type source_image: list[list[list[int]]]
    :param int XNEW: ``result_image`` width, pixels;
    :param int YNEW: ``result_image`` height, pixels;
    :param int | str edge: edge extrapolation mode:

        - ``edge=1`` or ``edge='repeat'``: repeat edge, like Photoshop;
        - ``edge=2`` or ``edge='wrap'``: wrap around;
        - ``edge=``other: extrapolate with zeroes.
          Alpha=0 correspond to transparent.
    :return: image, rescaled from ``X``, ``Y`` to ``XNEW``, ``YNEW`` size.
    :rtype: list[list[list[int]]]

    """

    # ↓ Determining source image sizes.
    Y, X, Z = (len(source_image), len(source_image[0]), len(source_image[0][0]))
    Z_COLOR = Z if Z == 1 or Z == 3 else min(Z - 1, 3)

    # ↓ Function was never FIR-optimized, but @lru_cache
    #   for source rows reading partially compensate for this.
    #   Effects starts at @lru_cache(maxsize=4), and seem to stabilize after maxsize=8.
    #   @lru_cache(maxsize=None) is a tiny yet statistically significant bit faster
    #   but  raise concerns regarding cache size for large images.
    #   On the Toad's behest and volution, maxsize was set
    #   to 8 for images bigger than 256 * 256 px, and None otherwise.
    cache_size = 8 if X * Y > 256 * 256 else None

    # ↓ Classic lru_cache syntax
    @lru_cache(maxsize=cache_size)
    def _pixel(x: int, y: int, edge: int | str, X: int, Y: int, Z: int) -> list[int]:
        """Local version of _src(x, y) with hardcoded source list name, good for caching."""
        return _src(source_image, x, y, edge, X, Y, Z)

    # ↓ Alternative lru_cache syntax
    # _pixel = lru_cache(maxsize=cache_size)(_pixel)

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
        if x == x1 and y == y1:
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

    # ↓ Resize factor
    x_resize = (X - 1) / (XNEW - 1)
    y_resize = (Y - 1) / (YNEW - 1)

    # ↓ Singe pass rescaling
    result_image = [[_baryc(x_resize * x, y_resize * y, edge, X, Y, Z) for x in range(XNEW)] for y in range(YNEW)]

    # ↓ Cache stats
    # print(f'{_pixel.cache_info()=} {(_pixel.cache_info()[0] / _pixel.cache_info()[1])=}')

    """
    # ↓ Single pass rescaling.
    #   Included here only for routine retesting of pixel() from __init__.py.
    from imin import pixel
    result_image = [[pixel(source_image, x_resize * x, y_resize * y, edge='repeat', method='barycentric') for x in range(XNEW)] for y in range(YNEW)]
    """

    return result_image


# ↓ Image rescaling, configurable interpolation, configurable edge modes
def rescale(source_image: list[list[list[int]]], XNEW: int, YNEW: int, edge: int | str = 'repeat', method: int | str = 'bilinear') -> list[list[list[int]]]:
    """Image rescaling with ``bilinear`` or ``barycentric`` depending on ``method``.

    :param source_image: source image 3D nested list,
        coordinate system match Photoshop, i.e. origin is top left corner,
        channels order is LA or RGBA from bottom to top;
    :type source_image: list[list[list[int]]]
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
    :return: image, rescaled from ``X``, ``Y`` to ``XNEW``, ``YNEW`` size.
    :rtype: list[list[list[int]]]

    """

    if method == 1 or method == 'bilinear':
        return bilinear(source_image, XNEW, YNEW, edge=edge)
    elif method == 2 or method == 'barycentric':
        return barycentric(source_image, XNEW, YNEW, edge=edge)
    else:
        raise ValueError('Allowed methods are: "bilinear" (1), "barycentric" (2)')
