"""Reading single image pixel, interpolated either bilinearly or barycentrically.

Usage
-----

::

    pixelvalue = pixel(source_image, x, y, edge, method)

where

- ``source_image``: source image 3D nested list; coordinate system match Photoshop,
i.e. origin is top left corner, channels order is LA or RGBA from 0 to top;
- ``x``: x coordinate of pixel being read;
- ``y``: y coordinate of pixel being read;
- ``edge``: edge extrapolation mode:
    - ``edge=1`` or ``edge='repeat'``: repeat edge, like Photoshop;
    - ``edge=2`` or ``edge='wrap'``;
    - ``edge=``other: extrapolate with zeroes;

- ``method``: pixel interpolation method:
    - ``method=0`` or ``method='nearest'``: nearest neighbour interpolation;
    - ``method=1`` or ``method='bilinear'``: bilinear interpolation;
    - ``method=2`` or ``method='barycentric'``: barycentric interpolation.

Return pixel value as list[int] of channel values.

----
**Main site**: `The Toad's Slimy Mudhole`_

.. _The Toad's Slimy Mudhole: https://dnyarri.github.io/

**imin** Git repositories: `@Github`_, `@Gitflic`_.

.. _@Github: https://github.com/Dnyarri/imin

.. _@Gitflic: https://gitflic.ru/project/dnyarri/imin

"""

__author__ = 'Ilya Razmanov'
__copyright__ = '(c) 2023-2026 Ilya Razmanov'
__credits__ = 'Ilya Razmanov'
__license__ = 'unlicense'
__version__ = '26.1.28.18'
__maintainer__ = 'Ilya Razmanov'
__email__ = 'ilyarazmanov@gmail.com'
__status__ = 'Development'

from operator import mul


# ↓ Pixel reading, different edge modes, nearest neighbour
def src(source_image: list[list[list[int]]], x: int | float, y: int | float, edge: int | str = 'repeat') -> list[int]:
    """Getting whole pixel from image list, nearest neighbour interpolation,
    returns list[channel] for pixel(x, y).

    :param source_image: source image 3D list, coordinate system match Photoshop,
    i.e. origin is top left corner, channels order is LA or RGBA from bottom to top;
    :type source_image: list[list[list[int]]]
    :param int x: x coordinate of pixel being read;
    :param int y: y coordinate of pixel being read;
    :param int | str edge: edge extrapolation mode:

        - `edge=1` or `edge='repeat'`: repeat edge, like Photoshop;
        - `edge=2` or `edge='wrap'`: wrap around;
        - `edge=`other: extrapolate with zeroes. Alpha=0 correspond to transparent.
    :return: pixel(x, y) value.
    :rtype: list[int]

    """

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


# ↓ Interpolated pixel reading, bilinear
def blin(source_image: list[list[list[int]]], x: float, y: float, edge: int | str) -> list[int]:
    """Returns bilinearly interpolated pixel(x, y).

    :param source_image: source image 3D list, coordinate system match Photoshop,
    i.e. origin is top left corner, channels order is LA or RGBA from bottom to top;
    :type source_image: list[list[list[int]]]
    :param float x: x coordinate of pixel being read;
    :param float y: y coordinate of pixel being read;
    :param int | str edge: edge extrapolation mode:

        - `edge=1` or `edge='repeat'`: repeat edge, like Photoshop;
        - `edge=2` or `edge='wrap'`: wrap around;
        - `edge=`other: extrapolate with zeroes. Alpha=0 correspond to transparent.
    :return: interpolated pixel(x, y) value.
    :rtype: list[int]

    """

    def _intaddup(a, b, c, d):
        return int(a + b + c + d)

    # ↓ Determining source image sizes.
    #   Y = len(source_image)
    #   X = len(source_image[0])
    Z = len(source_image[0][0])

    """ Square corners are enumerated according to scheme below:

          x0   x1
        ┼────┼────┤
     y0 │ 00 │ 10 │
        ┼────┼────┤
     y1 │ 01 │ 11 │
        └────┴────┘

    NOTE: Corners coordinates are calculated taking into account that
    for negative x and y values int(x) > x and int(y) > y correspondingly. """

    if x >= 0:
        x0 = int(x)
    else:
        x0 = int(x) - 1
    if y >= 0:
        y0 = int(y)
    else:
        y0 = int(y) - 1
    # ↓ In case of direct hit no interpolation required
    if x == x0 and y == y0:
        return src(source_image, x0, y0, edge)
    # ↓ In case of a miss interpolation ensues
    x1 = x0 + 1
    y1 = y0 + 1

    # ↓ Distance weights for pixels, packed as tuples for map() below
    w00 = (x1 - x) * (y1 - y)
    w01 = (x1 - x) * (y - y0)
    w10 = (x - x0) * (y1 - y)
    w11 = (x - x0) * (y - y0)
    wt00 = (w00,) * Z
    wt01 = (w01,) * Z
    wt10 = (w10,) * Z
    wt11 = (w11,) * Z

    # ↓ Reading corner pixels and scaling values according to weights above
    norm00 = [*map(mul, src(source_image, x0, y0, edge), wt00)]
    norm01 = [*map(mul, src(source_image, x0, y1, edge), wt01)]
    norm10 = [*map(mul, src(source_image, x1, y0, edge), wt10)]
    norm11 = [*map(mul, src(source_image, x1, y1, edge), wt11)]

    # ↓ Adding up scaled corners channel by channel
    pixelvalue = [*map(_intaddup, norm00, norm01, norm10, norm11)]

    """
    # ↓ List comprehension alternative to map.
    #   In single pass x5 upscaling execution time doubled vs. [*map()],
    #   so this alternative included here for educational purposes only.

    norm00 = [w00 * src(source_image, x0, y0, edge)[z] for z in range(Z)]
    norm01 = [w01 * src(source_image, x0, y1, edge)[z] for z in range(Z)]
    norm10 = [w10 * src(source_image, x1, y0, edge)[z] for z in range(Z)]
    norm11 = [w11 * src(source_image, x1, y1, edge)[z] for z in range(Z)]
    pixelvalue = [_intaddup(norm00[z], norm01[z], norm10[z], norm11[z]) for z in range(Z)]
    """

    return pixelvalue


# ↓ Interpolated pixel reading, barycentric
def baryc(source_image: list[list[list[int]]], x: float, y: float, edge: int | str) -> list[int]:
    """Returns barycentrically interpolated pixel(x, y).

    :param source_image: source image 3D list, coordinate system match Photoshop,
    i.e. origin is top left corner, channels order is LA or RGBA from bottom to top;
    :type source_image: list[list[list[int]]]
    :param float x: x coordinate of pixel being read;
    :param float y: y coordinate of pixel being read;
    :param int | str edge: edge extrapolation mode:

        - `edge=1` or `edge='repeat'`: repeat edge, like Photoshop;
        - `edge=2` or `edge='wrap'`: wrap around;
        - `edge=`other: extrapolate with zeroes. Alpha=0 correspond to transparent.
    :return: interpolated pixel(x, y) value.
    :rtype: list[int]

    """

    def _intaddup(a, b, c):
        return int(a + b + c)

    # ↓ Determining source image sizes.
    #   Y = len(source_image)
    #   X = len(source_image[0])
    Z = len(source_image[0][0])

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
    for negative x and y values int(x) > x and int(y) > y correspondingly. """

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
    p1 = src(source_image, x1, y1, edge)
    # ↓ In case of direct hit no interpolation required
    if x == x1 and y == y1:
        return p1
    # ↓ In case of a miss interpolation ensues
    p2 = src(source_image, x2, y2, edge)
    p3 = src(source_image, x3, y3, edge)
    p4 = src(source_image, x4, y4, edge)

    """ Now going to choose the diagonal for 2×2 pixel square folding based on
        comparing differences between pixels in 🡦 and 🡧 directions.
        Currently total sum of channels (excluding alpha) is used for comparison.
        The choice is questionable, but pro et contra may be given for any. """

    if abs(sum(p1[:Z_COLOR]) - sum(p3[:Z_COLOR])) < abs(sum(p2[:Z_COLOR]) - sum(p4[:Z_COLOR])):
        # ↓ ╲ diagonal
        if (x - x1) < (y - y1):
            # ↓ ◣ 1-3-4 triangle
            #   Doubled subtriangle area (i.e. base subrectangle area) is calculated,
            #   since it appears to be normalized to unit square already.
            a = x - x1
            b = y4 - y
            c = 1 - (a + b)
            at = (a,) * Z
            bt = (b,) * Z
            ct = (c,) * Z

            norm3 = [*map(mul, p3, at)]
            norm1 = [*map(mul, p1, bt)]
            norm4 = [*map(mul, p4, ct)]

            pixelvalue = [*map(_intaddup, norm1, norm3, norm4)]

            return pixelvalue

        # ↓ ◥ 1-2-3 triangle
        a = x2 - x
        b = y - y1
        c = 1 - (a + b)
        at = (a,) * Z
        bt = (b,) * Z
        ct = (c,) * Z

        norm1 = [*map(mul, p1, at)]
        norm3 = [*map(mul, p3, bt)]
        norm2 = [*map(mul, p2, ct)]

        pixelvalue = [*map(_intaddup, norm1, norm3, norm2)]

        return pixelvalue

    # ↓ ╱ diagonal
    if (x - x1) < (y3 - y):
        # ↓ ◤ 1-2-4 triangle
        a = x - x1
        b = y - y1
        c = 1 - (a + b)
        at = (a,) * Z
        bt = (b,) * Z
        ct = (c,) * Z

        norm2 = [*map(mul, p2, at)]
        norm4 = [*map(mul, p4, bt)]
        norm1 = [*map(mul, p1, ct)]

        pixelvalue = [*map(_intaddup, norm1, norm2, norm4)]

        return pixelvalue

    # ↓ ◢ 2-3-4 triangle
    a = x3 - x
    b = y4 - y
    c = 1 - (a + b)
    at = (a,) * Z
    bt = (b,) * Z
    ct = (c,) * Z

    norm4 = [*map(mul, p4, at)]
    norm2 = [*map(mul, p2, bt)]
    norm3 = [*map(mul, p3, ct)]

    pixelvalue = [*map(_intaddup, norm2, norm3, norm4)]

    return pixelvalue


# ↓ Interpolated pixel reading, general
def pixel(source_image: list[list[list[int]]], x: float, y: float, edge: int | str = 1, method: int | str = 1) -> list[int]:
    """Configurable method of reading interpolated pixel,
    returns list[channel] for pixel(x, y).

    :param source_image: source image 3D list, coordinate system match Photoshop,
    i.e. origin is top left corner, channels order is LA or RGBA from bottom to top;
    :type source_image: list[list[list[int]]]
    :param float x: x coordinate of pixel being read;
    :param float y: y coordinate of pixel being read;
    :param int | str edge: edge extrapolation mode:

        - `edge=1` or `edge='repeat'`: repeat edge, like Photoshop;
        - `edge=2` or `edge='wrap'`: wrap around;
        - `edge=`other: extrapolate with zeroes. Alpha=0 correspond to transparent.
    :param int | str method: pixel interpolation method:

        - `method=2` or `method='barycentric'`: barycentric interpolation;
        - `method=1` or `method='bilinear'`: bilinear interpolation;
        - `method=0` or `method='nearest'`: nearest neighbour interpolation.
    :return: interpolated pixel(x, y) value.
    :rtype: list[int]

    """

    if method == 1 or method == 'bilinear':
        return blin(source_image, x, y, edge)
    elif method == 2 or method == 'barycentric':
        return baryc(source_image, x, y, edge)
    elif method == 0 or method == 'nearest':
        return src(source_image, x, y, edge)
    else:
        raise ValueError('Allowed methods are 0, 1, 2')
