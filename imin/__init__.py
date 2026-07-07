"""Reading single image pixel, interpolated either bilinearly or barycentrically.

Usage
-----

::

    pixelvalue = pixel(source_image, x, y, edge, method)

where:

- ``source_image``: source image 3D nested list; coordinate system match Photoshop,
i.e. origin is top left corner, channels order is LA or RGBA from 0 to top;
- ``x``: x coordinate of pixel being read;
- ``y``: y coordinate of pixel being read;
- ``edge``: edge extrapolation mode:
    - ``edge=1`` or ``edge='repeat'``: repeat edge, like Photoshop;
    - ``edge=2`` or ``edge='wrap'``;
    - ``edge=``other: extrapolate with zeroes. Alpha=0 means transparent.

- ``method``: pixel interpolation method:
    - ``method=0`` or ``method='nearest'``: nearest neighbour interpolation;
    - ``method=1`` or ``method='bilinear'``: bilinear interpolation;
    - ``method=2`` or ``method='barycentric'``: barycentric interpolation.

Return pixel value as list[int] of channel values.

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
__copyright__ = '(c) 2023-2026 Ilya Razmanov'
__credits__ = 'Ilya Razmanov'
__license__ = 'unlicense'
__version__ = '26.7.7.17'
__maintainer__ = 'Ilya Razmanov'
__email__ = 'ilyarazmanov@gmail.com'
__status__ = 'Development'

from operator import mul


# ↓ Pixel reading, nearest neighbour interpolation, configurable edge modes
def src(source_image: list[list[list[int]]], x: int | float, y: int | float, edge: int | str) -> list[int]:
    """Reading pixel(x, y) list from image nested list, nearest neighbour interpolation.

    :param source_image: source image 3D nested list,
        coordinate system match Photoshop, i.e. origin is top left corner,
        channels order is LA or RGBA from bottom to top;
    :type source_image: list[list[list[int]]]
    :param int x: ``x`` coordinate of pixel being read;
    :param int y: ``y`` coordinate of pixel being read;
    :param int | str edge: edge extrapolation mode:

        - ``edge=1`` or ``edge='repeat'``: repeat edge, like Photoshop;
        - ``edge=2`` or ``edge='wrap'``: wrap around;
        - ``edge=``other: extrapolate with zeroes.
          Alpha=0 correspond to transparent.
    :return: pixel(x, y) value.
    :rtype: list[int]

    """

    # ↓ Determining source image sizes.
    Y, X, Z = (len(source_image), len(source_image[0]), len(source_image[0][0]))
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
        # ↓ Fill with zeroes. For images with transparency, edge transparency extrapolated as zeroes,
        #   while edge color as "repeat edge". This eliminates black edge artifacts.
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


# ↓ Pixel reading, bilinear interpolation, configurable edge modes
def _blin(source_image: list[list[list[int]]], x: float, y: float, edge: int | str) -> list[int]:
    """Returns bilinearly interpolated pixel(x, y).

    :param source_image: source image 3D list,
        coordinate system match Photoshop, i.e. origin is top left corner,
        channels order is LA or RGBA from bottom to top;
    :type source_image: list[list[list[int]]]
    :param float x: ``x`` coordinate of pixel being read;
    :param float y: ``y`` coordinate of pixel being read;
    :param int | str edge: edge extrapolation mode:

        - ``edge=1`` or ``edge='repeat'``: repeat edge, like Photoshop;
        - ``edge=2`` or ``edge='wrap'``: wrap around;
        - ``edge=``other: extrapolate with zeroes.
          Alpha=0 correspond to transparent.
    :return: interpolated pixel(x, y) value.
    :rtype: list[int]

    """

    def _intaddup_4(a, b, c, d):
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

    NOTE: Corners coordinates are calculated taking into account the fact that
    for negative x and y values int(x) > x and int(y) > y correspondingly. """

    if x >= 0:
        x0 = int(x)
    else:
        x0 = int(x) - 1
    if y >= 0:
        y0 = int(y)
    else:
        y0 = int(y) - 1

    # ↓ Starting corner pixels reading
    pix00 = src(source_image, x0, y0, edge)

    # ↓ In case of direct hit no interpolation required
    if x == x0 and y == y0:
        return pix00

    # ↓ In case of a miss interpolation ensues
    x1 = x0 + 1
    y1 = y0 + 1
    pix01 = src(source_image, x0, y1, edge)
    pix10 = src(source_image, x1, y0, edge)
    pix11 = src(source_image, x1, y1, edge)

    # ↓ Distance weights "w" for corner pixels
    w00 = (x1 - x) * (y1 - y)
    w01 = (x1 - x) * (y - y0)
    w10 = (x - x0) * (y1 - y)
    w11 = (x - x0) * (y - y0)

    # ↓ Packing weights "w" as tuples "wt" for map() below
    wt00 = (w00,) * Z
    wt01 = (w01,) * Z
    wt10 = (w10,) * Z
    wt11 = (w11,) * Z

    # ↓ Scaling corner pixels values "pix" according to weights above
    norm00 = [*map(mul, pix00, wt00)]
    norm01 = [*map(mul, pix01, wt01)]
    norm10 = [*map(mul, pix10, wt10)]
    norm11 = [*map(mul, pix11, wt11)]

    # ↓ Adding up scaled corner pixels "norm" channel by channel
    pixelvalue = [*map(_intaddup_4, norm00, norm01, norm10, norm11)]

    """
    # ↓ List comprehension alternative to map.
    #   In single pass x5 upscaling execution time appeared to be doubled
    #   vs. [*map()], so this alternative is described here
    #   for illustration purposes only.

    norm00 = [w00 * src(source_image, x0, y0, edge)[z] for z in range(Z)]
    norm01 = [w01 * src(source_image, x0, y1, edge)[z] for z in range(Z)]
    norm10 = [w10 * src(source_image, x1, y0, edge)[z] for z in range(Z)]
    norm11 = [w11 * src(source_image, x1, y1, edge)[z] for z in range(Z)]
    pixelvalue = [_intaddup_4(norm00[z], norm01[z], norm10[z], norm11[z]) for z in range(Z)]
    """

    return pixelvalue


# ↓ Pixel reading, barycentric interpolation, configurable edge modes
def _baryc(source_image: list[list[list[int]]], x: float, y: float, edge: int | str) -> list[int]:
    """Returns barycentrically interpolated pixel(x, y).

    :param source_image: source image 3D list,
        coordinate system match Photoshop, i.e. origin is top left corner,
        channels order is LA or RGBA from bottom to top;
    :type source_image: list[list[list[int]]]
    :param float x: ``x`` coordinate of pixel being read;
    :param float y: ``y`` coordinate of pixel being read;
    :param int | str edge: edge extrapolation mode:

        - ``edge=1`` or ``edge='repeat'``: repeat edge, like Photoshop;
        - ``edge=2`` or ``edge='wrap'``: wrap around;
        - ``edge=``other: extrapolate with zeroes.
          Alpha=0 correspond to transparent.
    :return: interpolated pixel(x, y) value.
    :rtype: list[int]

    """

    def _intaddup_3(a, b, c):
        return int(a + b + c)

    # ↓ Determining source image sizes.
    #   Y = len(source_image)
    #   X = len(source_image[0])
    Z = len(source_image[0][0])

    # ↓ For calculation of pixel color difference between corners,
    #   number of channels minus alpha is required.
    #   Potential channels above RGBA are discarded.
    Z_COLOR = Z if Z == 1 or Z == 3 else min(Z - 1, 3)

    """ Square corners are enumerated according to Soviet Army «snail» scheme
        ┌───┬───┐
        │ 1 │ 2 │
        ├───┼───┤
        │ 4 │ 3 │
        └───┴───┘
        and square divided onto two triangles by either 1-3 [⧅] or 
        2-4 [⧄] diagonal depending on what color difference is bigger
        (i.e. on directional local contrast). 

        Each triangle is right-angled and takes 0.5 of area of
        1×1 length unit square (i.e. 2×2 pixel number square),
        that greatly simplifies calculation.

    NOTE: Corners coordinates are calculated taking into account the fact that
    for negative x and y values int(x) > x and int(y) > y correspondingly. """

    if x >= 0:
        x1 = int(x)
    else:
        x1 = int(x) - 1
    if y >= 0:
        y1 = int(y)
    else:
        y1 = int(y) - 1

    # ↓ Starting corner pixels reading
    pix1 = pixel(source_image, x1, y1, edge)

    # ↓ In case of direct hit no interpolation required
    if x == x1 and y == y1:
        return pix1

    # ↓ In case of a miss interpolation ensues
    x2 = x1 + 1
    y2 = y1
    x3 = x2
    y3 = y1 + 1
    x4 = x1
    y4 = y3
    pix2 = pixel(source_image, x2, y2, edge)
    pix3 = pixel(source_image, x3, y3, edge)
    pix4 = pixel(source_image, x4, y4, edge)

    """ Now going to choose the diagonal for 2×2 pixel square folding based on
        comparing differences between pixels in 🡦 and 🡧 directions.
        Currently total sum of channel values (excluding alpha)
        is used for comparison.
        The choice is questionable, but pro et contra may be given for any. """

    diff13 = abs(sum(pix1[:Z_COLOR]) - sum(pix3[:Z_COLOR]))
    diff24 = abs(sum(pix2[:Z_COLOR]) - sum(pix4[:Z_COLOR]))

    if diff13 < diff24:
        # ↓ ⧅ diagonal
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

            norm3 = [*map(mul, pix3, at)]
            norm1 = [*map(mul, pix1, bt)]
            norm4 = [*map(mul, pix4, ct)]

            pixelvalue = [*map(_intaddup_3, norm1, norm3, norm4)]

            return pixelvalue

        if (x - x1) > (y - y1):
            # ↓ ◥ 1-2-3 triangle
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

    if diff13 > diff24:
        # ↓ ⧄ diagonal
        if (x - x1) < (y3 - y):
            # ↓ ◤ 1-2-4 triangle
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
            # ↓ ◢ 2-3-4 triangle
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

    """ Take notice that criteria above do not comprise
        "diagonal contrasts are equal" or "interpolated pixel is on diagonal,
        precisely" variants.
        If none of the criteria above satisfied, situation is considered
        "symmetrical", and bilinear interpolation ensue to avoid
        introducing asymmetrical artifacts. """

    def _intaddup_4(a, b, c, d):
        return int(a + b + c + d)

    # ↓ Distance weights "w" for corner pixels
    w1 = (x3 - x) * (y3 - y)
    w2 = (x - x4) * (y4 - y)
    w3 = (x - x1) * (y - y1)
    w4 = (x2 - x) * (y - y2)

    # ↓ Packing weights "w" as tuples "wt" for map() below
    wt1 = (w1,) * Z
    wt2 = (w2,) * Z
    wt3 = (w3,) * Z
    wt4 = (w4,) * Z

    # ↓ Scaling corner pixels values "pix" according to weights above
    norm1 = [*map(mul, pix1, wt1)]
    norm2 = [*map(mul, pix2, wt2)]
    norm3 = [*map(mul, pix3, wt3)]
    norm4 = [*map(mul, pix4, wt4)]

    # ↓ Adding up scaled corner pixels "norm" channel by channel
    pixelvalue = [*map(_intaddup_4, norm1, norm4, norm2, norm3)]

    return pixelvalue


# ↓ Pixel reading, configurable interpolation, configurable edge modes
def pixel(source_image: list[list[list[int]]], x: float, y: float, edge: int | str = 'repeat', method: int | str = 'bilinear') -> list[int]:
    """Configurable method of reading interpolated pixel(x, y).

    :param source_image: source image 3D list,
        coordinate system match Photoshop, i.e. origin is top left corner,
        channels order is LA or RGBA from bottom to top;
    :type source_image: list[list[list[int]]]
    :param float x: ``x`` coordinate of pixel being read;
    :param float y: ``y`` coordinate of pixel being read;
    :param int | str edge: edge extrapolation mode:

        - ``edge=1`` or ``edge='repeat'``: repeat edge, like Photoshop;
        - ``edge=2`` or ``edge='wrap'``: wrap around;
        - ``edge=``other: extrapolate with zeroes.
          Alpha=0 correspond to transparent.
    :param int | str method: pixel interpolation method:

        - ``method=2`` or ``method='barycentric'``: barycentric interpolation;
        - ``method=1`` or ``method='bilinear'``: bilinear interpolation;
        - ``method=0`` or ``method='nearest'``: nearest neighbour interpolation.
    :return: interpolated pixel(x, y) value.
    :rtype: list[int]

    """

    if method == 1 or method == 'bilinear':
        return _blin(source_image, x, y, edge)
    elif method == 2 or method == 'barycentric':
        return _baryc(source_image, x, y, edge)
    elif method == 0 or method == 'nearest':
        return src(source_image, x, y, edge)
    else:
        raise ValueError('Allowed methods are: "bilinear" (1), "barycentric" (2), "nearest" (0)')
