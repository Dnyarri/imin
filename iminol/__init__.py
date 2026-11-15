"""Light version of **imin** image interpolation methods, not optimized,
always in motion, poorly documented, *totally untested und highly dangerous!*"""

__author__ = 'Ilya Razmanov'
__copyright__ = '(c) 2025-2026 Ilya Razmanov'
__credits__ = 'Ilya Razmanov'
__license__ = 'unlicense'
__version__ = '26.11.15.17'
__maintainer__ = 'Ilya Razmanov'
__email__ = 'ilyarazmanov@gmail.com'
__status__ = 'Development'

from concurrent.futures import ThreadPoolExecutor
from operator import mul
from typing import Literal, Self


class Picture:
    """Contains image as 3D list[list[list[int]]], and various methods
    to read a pixel=image(x, y), interpolate it, or transform whole image
    using one of interpolation methods.

    Usage
    -----

    ::

        picture = Picture(image_data, maxcolors)

    where:

    - ``image_data``: list[list[list[int]]] image of rows of pixels of channels;
    - ``maxcolors``: int maximal value of colors per channel,
        either 255 for 8 bit or 65535 for 16 bit images.

    then follow **Main methods** section below.

    Main methods:
    -------------

    - .. function:: ``data()``:
            return list[list[list[int]]] image of rows of pixels of channels.

    - .. function:: ``maxcolors()``:
            return int maximal value of colors per channel.

    - .. function:: ``size()``:
            return tuple[int, int, int] of image sizes.

    - .. function:: ``pixel(x: float, y: float, edge, method)``:
        return pixel having x, y coordinates, as list(channel: int).

        Edge extrapolation using:
            - ``edge='repeat'``: repeat edge, like Photoshop;
            - ``edge='wrap'``: wrap around;
            - ``edge=``other: extrapolate with zeroes.
                Alpha=0 correspond to transparent.

        Interpolation using:
            - ``method="bilinear"``: bilinear interpolation;
            - ``method="barycentric"``: barycentric interpolation.

    - .. function:: ``rescale(width: int, height: int, method)``:
        chainable rescale ``self`` to new ``width`` and ``height``.

    - .. function:: ``scale(width: int, height: int, method)``:
        return rescaled image as list(list(pixel)), having new ``width`` and ``height``,
        and ``maxcolors``. Does not change ``self``.

    - .. function:: ``rotate(angle, edge, method)``:
        image rotation by ``angle`` degrees counterclockwise.

    """

    def __init__(self, *input: tuple[list[list[list[int]]], int] | tuple[tuple[list[list[list[int]]], int]]):
        """Initializes a new instance of ``Picture`` out of image data list and colors per channel maximum.

        :param input: ``tuple(image_data, maxcolors,)``, which may have extra tuple() on it;
        :type input: tuple[list[list[list[int]]], int] | tuple[tuple[list[list[list[int]]]
        :param image_data: image of rows of pixels of channel values;
        :type image_data: list[list[list[int]]]
        :param int maxcolors: maximal value of colors per channel,
            either 255 for 8 bit or 65535 for 16 bit images.

        """
        if len(input) == 1:  # in case of extra tuple on the top of input tuple
            input = input[0]
        self.image_data: list[list[list[int]]] = input[0]
        """Image data nested 3D list."""
        self.MAXCOLORS: int = input[1]
        """Maximal color value per channel, either 255, or 65535."""
        self.Y = len(self.image_data)
        """Image height, px."""
        self.X = len(self.image_data[0])
        """Image width, px."""
        self.Z = len(self.image_data[0][0])
        """Number of channels."""
        self.SIZE = (
            self.X,
            self.Y,
            self.Z,
        )
        """Image nested 3D list sizes (X, Y, Z,)."""

    def data(self) -> list[list[list[int]]]:
        """Image data nested 3D list."""
        return self.image_data

    def maxcolors(self) -> int:
        """Maximal color value per channel (int), typically either 255, or 65535."""
        return self.MAXCOLORS

    def size(self) -> tuple[int, int, int]:
        """Image nested 3D list sizes (X, Y, Z,)."""
        return self.SIZE

    def src(self, x: float, y: float, edge: Literal['zero', 'repeat', 'wrap'] = 'repeat') -> list[int]:
        """Whole pixel from image list, nearest neighbour interpolation,
        configurable edge extrapolation, returns list[channel] for pixel(x, y).

        :param float x: ``x`` coordinate of pixel being read;
        :param float y: ``y`` coordinate of pixel being read;
        :param str | int edge: edge extrapolation mode:

            - ``edge='repeat'``: repeat edge, like Photoshop;
            - ``edge='wrap'``: wrap around;
            - ``edge=``other: extrapolate with zeroes.
              Alpha=0 correspond to transparent.
        :return: pixel(x, y) value.
        :rtype: list[int]

        """

        X, Y, Z = self.size()
        Z_COLOR = Z if Z == 1 or Z == 3 else min(Z - 1, 3)  # Number of color channels, alpha excluded.
        if edge == 1 or edge == 'repeat':
            # ↓ Repeat edge.
            cx = min(X - 1, max(0, int(x)))
            cy = min(Y - 1, max(0, int(y)))
            return self.image_data[cy][cx]
        elif edge == 2 or edge == 'wrap':
            # ↓ Wrap around.
            cx = int(x) % X
            cy = int(y) % Y
            return self.image_data[cy][cx]
        else:
            # ↓ Zeroes.
            if x < 0 or y < 0 or x > X - 1 or y > Y - 1:  # Edge
                if Z == 1 or Z == 3:
                    return [0] * Z
                else:
                    cx = min(X - 1, max(0, int(x)))
                    cy = min(Y - 1, max(0, int(y)))
                    # ↓ Mixing extrapolated source color with zero alpha
                    #   to avoid black ghosts.
                    return [*self.image_data[cy][cx][:Z_COLOR], 0]
            else:  # Not edge
                return self.image_data[int(y)][int(x)]

    def blin(self, x: float, y: float, edge: Literal['zero', 'repeat', 'wrap'] = 'repeat') -> list[int]:
        """Returns bilinearly interpolated pixel(x, y).

        :param float x: ``x`` coordinate of pixel being read;
        :param float y: ``y`` coordinate of pixel being read;
        :param str | int edge: edge extrapolation mode:

            - ``edge='repeat'``: repeat edge, like Photoshop;
            - ``edge='wrap'``: wrap around;
            - ``edge=``other: extrapolate with zeroes.
                Alpha=0 correspond to transparent.
        :return: interpolated pixel(x, y) value.
        :rtype: list[int]

        .. note:: Square corners are enumerated according to Soviet Army «snail» scheme

        | ``┌───┬───┐``
        | ``│ 1 │ 2 │``
        | ``├───┼───┤``
        | ``│ 4 │ 3 │``
        | ``└───┴───┘``

        and direct one-pass 2D bilinear interpolation applied.

        Corners coordinates are calculated taking into account the fact that
        for negative x and y values ``int(x) > x`` and ``int(y) > y ``correspondingly."""

        def _intaddup_4(a, b, c, d):
            return int(a + b + c + d)

        Z = self.Z

        if x >= 0:
            x1 = int(x)
        else:
            x1 = int(x) - 1
        if y >= 0:
            y1 = int(y)
        else:
            y1 = int(y) - 1

        pix1 = self.src(x1, y1, edge)
        if x == x1 and y == y1:
            return pix1
        x2 = x1 + 1
        y2 = y1
        x3 = x2
        y3 = y1 + 1
        x4 = x1
        y4 = y3

        pix2 = self.src(x2, y2, edge)
        pix3 = self.src(x3, y3, edge)
        pix4 = self.src(x4, y4, edge)

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

    def baryc(self, x: float, y: float, edge: Literal['zero', 'repeat', 'wrap'] = 'repeat') -> list[int]:
        """Returns barycentrically interpolated pixel(x, y).

        :param float x: ``x`` coordinate of pixel being read;
        :param float y: ``y`` coordinate of pixel being read;
        :param str | int edge: edge extrapolation mode:

            - ``edge='repeat'``: repeat edge, like Photoshop;
            - ``edge='wrap'``: wrap around;
            - ``edge=``other: extrapolate with zeroes.
              Alpha=0 correspond to transparent.
        :return: interpolated pixel(x, y) value.
        :rtype: list[int]

        .. note:: Square corners are enumerated according to Soviet Army «snail» scheme

        | ``┌───┬───┐``
        | ``│ 1 │ 2 │``
        | ``├───┼───┤``
        | ``│ 4 │ 3 │``
        | ``└───┴───┘``

        and square divided onto two triangles by either 1-3 [⧅] or
        2-4 [⧄] diagonal depending on what color difference is bigger
        (i.e. on directional local contrast).

        Each triangle is right-angled and takes 0.5 of area of
        1×1 length unit square (i.e. 2×2 pixel number square),
        that greatly simplifies calculation.

        Corners coordinates are calculated taking into account the fact that
        for negative x and y values ``int(x) > x`` and ``int(y) > y ``correspondingly."""

        def _intaddup_3(a, b, c):
            return int(a + b + c)

        Z = self.Z
        Z_COLOR = Z if Z == 1 or Z == 3 else min(Z - 1, 3)
        if x >= 0:
            x1 = int(x)
        else:
            x1 = int(x) - 1
        if y >= 0:
            y1 = int(y)
        else:
            y1 = int(y) - 1

        pix1 = self.src(x1, y1, edge)
        if x == x1 and y == y1:
            return pix1
        x2 = x1 + 1
        y2 = y1
        x3 = x2
        y3 = y1 + 1
        x4 = x1
        y4 = y3

        pix2 = self.src(x2, y2, edge)
        pix3 = self.src(x3, y3, edge)
        pix4 = self.src(x4, y4, edge)

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

        """ If none of the criteria above satisfied, none of diagonals is "best", so
            bilinear interpolation ensue to avoid introducing asymmetrical artifacts. """

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

    def pixel(self, x: float, y: float, edge: Literal['zero', 'repeat', 'wrap'] = 'repeat', method: Literal['nearest', 'bilinear', 'barycentric'] = 'bilinear') -> list[int]:
        """Configurable method of reading interpolated pixel,
        returns list[channel] for pixel(x, y).

        :param float x: ``x`` coordinate of pixel being read;
        :param float y: ``y`` coordinate of pixel being read;
        :param str | int edge: edge extrapolation mode:

            - ``edge='repeat'``: repeat edge, like Photoshop;
            - ``edge='wrap'``: wrap around;
            - ``edge=``other: extrapolate with zeroes.
                Alpha=0 correspond to transparent.
        :param str | int method: pixel interpolation method:

            - ``method='barycentric'``: barycentric interpolation;
            - ``method='bilinear'``: bilinear interpolation;
            - ``method=0`` or ``method='nearest'``: nearest neighbour interpolation.
        :return: interpolated pixel(x, y) value.
        :rtype: list[int]

        """

        if method == 0 or method == 'nearest':
            return self.src(x, y, edge)
        if method == 1 or method == 'bilinear':
            return self.blin(x, y, edge)
        if method == 2 or method == 'barycentric':
            return self.baryc(x, y, edge)

    def scale(self, width: int, height: int, edge: Literal['zero', 'repeat', 'wrap'] = 'repeat', method: Literal['nearest', 'bilinear', 'barycentric'] = 'bilinear', ego: bool = False) -> Self:
        """Rescale **``self``** image (chainable method), using bilinear or barycentric interpolation depending on ``method``.

        :param int width: updated **``self``** image width, pixels;
        :param int height: updated **``self``** image height, pixels;
        :param str | int edge: edge extrapolation mode:

            - ``edge='repeat'``: repeat edge, like Photoshop;
            - ``edge='wrap'``: wrap around;
            - ``edge=``other: extrapolate with zeroes.
                Alpha=0 correspond to transparent.
        :param str | int method: interpolation method

            - ``method='barycentric'``: barycentric interpolation;
            - ``method='bilinear'``: bilinear interpolation.
        :param bool ego: whether return ``self`` or new ``Picture``.
        :return: `Picture` instance, containing image, rescaled to
        new ``width`` and ``height``, and ``maxcolors``.
        :rtype: Picture

        """

        x_resize = (self.X - 1) / (width - 1)
        y_resize = (self.Y - 1) / (height - 1)

        def _row(y):
            return [self.pixel(x_resize * x, y_resize * y, method=method) for x in range(width)]

        # ↓ Singe pass rescaling
        with ThreadPoolExecutor() as row_executor:
            merge = row_executor.map(_row, range(height))
        if ego:
            self.image_data = list(merge)
            return self
        else:
            new_image_data = list(merge)
            return Picture(
                new_image_data,
                self.maxcolors,
            )

    def rotate(self, angle: float, edge: Literal['zero', 'repeat', 'wrap'] = 'repeat', method: Literal['nearest', 'bilinear', 'barycentric'] = 'bilinear', ego: bool = False) -> Self:
        """Image rotation by means of displacement with algorithmic map, using bilinear or barycentric interpolation depending on ``method`` switch.

        :param float angle: rotation angle, degree counterclockwise;
        :param str | int edge: edge extrapolation mode:

            - ``edge='repeat'``: repeat edge, like Photoshop;
            - ``edge='wrap'``: wrap around;
            - ``edge=``other: extrapolate with zeroes.
              Alpha=0 correspond to transparent.
        :param str | int method: interpolation method

            - ``method='barycentric'``: barycentric interpolation;
            - ``method='bilinear'``: bilinear interpolation;
        :param bool ego: whether return ``self`` or new ``Picture``.
        :return: `Picture` instance, containing image rotated
        by ``angle`` degrees counterclockwise, and ``maxcolors``.
        :rtype: Picture

        """

        from math import cos, radians, sin

        SIN = sin(radians(angle))
        COS = cos(radians(angle))

        width = int(abs(COS * self.X) + abs(SIN * self.Y))
        height = int(abs(SIN * self.X) + abs(COS * self.Y))

        def _fx(x, y):
            return ((x - (width / 2)) * COS) - ((y - (height / 2)) * SIN) + (self.X / 2)

        def _fy(x, y):
            return ((x - (width / 2)) * SIN) + ((y - (height / 2)) * COS) + (self.Y / 2)

        def _row(y):
            return [self.pixel(_fx(x, y), _fy(x, y), edge, method) for x in range(width)]

        # ↓ Singe pass rotation
        with ThreadPoolExecutor() as row_executor:
            merge = row_executor.map(_row, range(height))
        if ego:
            self.image_data = list(merge)
            return self
        else:
            new_image_data = list(merge)
            return Picture(
                new_image_data,
                self.maxcolors,
            )
