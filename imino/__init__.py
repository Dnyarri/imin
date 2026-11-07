"""Image interpolation methods, currently bilinear and barycentric,
poorly documented, utterly untested und highly dangerous!"""

__author__ = 'Ilya Razmanov'
__copyright__ = '(c) 2025-2026 Ilya Razmanov'
__credits__ = 'Ilya Razmanov'
__license__ = 'unlicense'
__version__ = '26.11.7.7'
__maintainer__ = 'Ilya Razmanov'
__email__ = 'ilyarazmanov@gmail.com'
__status__ = 'Development'

from operator import mul


class Picture:
    """Various ways to read a pixel=image(x, y) from 3D list[list[list[int]]],
    interpolate it, or transform whole image using one of interpolation methods.

    Usage
    -----

    ::

        picture = Picture(image_data, maxcolors)

    then::

        result_picture = Picture(picture.scale(width, height, method))

    or::

        result_picture = Picture(picture.rotate(angle, edge, method))

    or::

        result_picture = Picture(picture.displace(fx, fy, width, height, edge, method))

    Methods:
    --------

        - ``pixel(x: float, y: float, method)``:
            return pixel having x, y coordinates, as list(channel: int), interpolated using:
                - ``method=1`` or ``method="bilinear"``: bilinear interpolation;
                - ``method=2`` or ``method="barycentric"``: barycentric interpolation.

        - ``rescale(width: int, height: int, method)``:
            chainable rescale ``self`` to new ``width`` and ``height``, interpolated using:
                - ``method=1` or `method="bilinear"``: bilinear interpolation;
                - ``method=2` or `method="barycentric"``: barycentric interpolation.

        - ``scale(width: int, height: int, method)``:
            return rescaled image as list(list(pixel)), having new ``width`` and ``height``, interpolated using:
                - ``method=1` or `method="bilinear"``: bilinear interpolation;
                - ``method=2` or `method="barycentric"``: barycentric interpolation.

            and ``maxcolors``. Does not change ``self``.

        - ``displace(fx, fy, width, height, edge, method)``:
            arbitrary pixels displacement according to ``fx(x, y)`` and ``fy(x, y)`` functions,
            edge extrapolation with:
                - ``edge=1`` or ``edge='repeat'``: repeat edge, like Photoshop;
                - ``edge=2`` or ``edge='wrap'``: wrap around;
                - ``edge=``other: extrapolate with zeroes.
                Alpha=0 correspond to transparent.
            interpolation using:
                - ``method=1` or `method="bilinear"``: bilinear interpolation;
                - ``method=2` or `method="barycentric"``: barycentric interpolation.

            ``width`` and ``height`` of resulting image to be determined by the developer.

        - ``rotate(angle, edge, method)``:
            image rotation by ``angle`` degrees counterclockwise, edge extrapolation with:
                - ``edge=1`` or ``edge='repeat'``: repeat edge, like Photoshop;
                - ``edge=2`` or ``edge='wrap'``: wrap around;
                - ``edge=``other: extrapolate with zeroes.
                Alpha=0 correspond to transparent.
            interpolation using:
                - ``method=1` or `method="bilinear"``: bilinear interpolation;
                - ``method=2` or `method="barycentric"``: barycentric interpolation.

    """

    def __init__(self, *input: tuple[list[list[list[int]]], int] | tuple[tuple[list[list[list[int]]], int]]):
        """Initializes a new instance of ``Picture`` out of image data list and colors per channel maximum.

        :param *input: ``tuple(image_data, maxcolors,)``, see below:
        :type *input: tuple[list[list[list[int]]], int] or tuple[tuple[list[list[list[int]]]
        :param image_data: image of rows of pixels of channel values;
        :type image_data: list[list[list[int]]]
        :param int maxcolors: maximal value of colors per channel,
            either 255 for 8 bit or 65535 for 16 bit images.

        """
        if len(input) == 1:  # in case of extra tuple on the top of input tuple
            input = input[0]
        self.image_data, self.maxcolors = input
        self.Y = len(self.image_data)
        """Image height, px."""
        self.X = len(self.image_data[0])
        """Image width, px."""
        self.Z = len(self.image_data[0][0])
        """Number of channels."""

    def data(self) -> list[list[list[int]]]:
        """Image data nested 3D list."""
        return self.image_data

    def size(self) -> tuple[int, int, int]:
        """Image nested 3D list sizes X, Y, Z."""
        Y, X, Z = len(self.image_data), len(self.image_data[0]), len(self.image_data[0][0])
        return (X, Y, Z)

    def maxcolors(self) -> int:
        """Maximal color value per channel (int), typically either 255, or 65535;"""
        return self.maxcolors

    def src(self, x: float, y: float, edge: int | str = 'repeat') -> list[int]:
        """Whole pixel from image list, nearest neighbour interpolation,
        returns list[channel] for pixel(x, y).

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

        X, Y, Z = self.size()
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
            if x < 0 or y < 0 or x > X - 1 or y > Y - 1:
                return [0] * Z
            else:
                return self.image_data[int(y)][int(x)]

    def blin(self, x: float, y: float, edge: int | str) -> list[int]:
        """Returns bilinearly interpolated pixel(x, y).

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

        def _intaddup(a, b, c, d):
            return int(a + b + c + d)

        Z = self.Z

        if x >= 0:
            x0 = int(x)
        else:
            x0 = int(x) - 1
        if y >= 0:
            y0 = int(y)
        else:
            y0 = int(y) - 1
        # ↓ Starting corner pixels reading
        pix00 = self.src(x0, y0, edge)
        # ↓ In case of direct hit no interpolation required
        if x == x0 and y == y0:
            return pix00
        # ↓ In case of a miss interpolation ensues
        x1 = x0 + 1
        y1 = y0 + 1
        w00 = (x1 - x) * (y1 - y)
        w01 = (x1 - x) * (y - y0)
        w10 = (x - x0) * (y1 - y)
        w11 = (x - x0) * (y - y0)
        wt00 = (w00,) * Z
        wt01 = (w01,) * Z
        wt10 = (w10,) * Z
        wt11 = (w11,) * Z
        norm00 = [*map(mul, pix00, wt00)]
        norm01 = [*map(mul, self.src(x0, y1, edge), wt01)]
        norm10 = [*map(mul, self.src(x1, y0, edge), wt10)]
        norm11 = [*map(mul, self.src(x1, y1, edge), wt11)]
        pixelvalue = [*map(_intaddup, norm00, norm01, norm10, norm11)]
        return pixelvalue

    def baryc(self, x: float, y: float, edge: int | str) -> list[int]:
        """Returns barycentrically interpolated pixel(x, y).

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

        """ If none of the criteria above satisfied, bilinear interpolation ensue
            to avoid introducing asymmetrical artifacts. """

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

    def pixel(self, x: float, y: float, edge: int | str, method: int | str) -> list[int]:
        """Configurable method of reading interpolated pixel,
        returns list[channel] for pixel(x, y).

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

        if method == 0 or method == 'nearest':
            return self.src(x, y, edge)
        if method == 1 or method == 'bilinear':
            return self.blin(x, y, edge)
        if method == 2 or method == 'barycentric':
            return self.baryc(x, y, edge)

    def rescale(self, width: int, height: int, edge: int | str = 'repeat', method: int | str = 'bilinear'):
        """Rescale **``self``** image (chainable method), using bilinear or barycentric interpolation depending on ``method``.

        :param int width: updated **``self``** image width, pixels;
        :param int height: updated **``self``** image height, pixels;
        :param int | str edge: edge extrapolation mode:

            - ``edge=1`` or ``edge='repeat'``: repeat edge, like Photoshop;
            - ``edge=2`` or ``edge='wrap'``: wrap around;
            - ``edge=``other: extrapolate with zeroes.
                Alpha=0 correspond to transparent.
        :param int | str method: interpolation method

            - ``method=2`` or ``method='barycentric'``: barycentric interpolation;
            - ``method=1`` or ``method='bilinear'``: bilinear interpolation.

        .. warning:: ``rescale`` function, unlike ``scale`` one, **overwrites**
            existing image rather than return new one!

        """

        from .rescale import rescale as _rescale

        self.image_data = _rescale(self.image_data, width, height, edge, method)
        return self

    def scale(self, width: int, height: int, edge: int | str = 'repeat', method: int | str = 'bilinear'):
        """Return image, rescaled using bilinear or barycentric interpolation depending on ``method``.

        :param int width: resulting image width, pixels;
        :param int height: resulting image height, pixels;
        :param int | str edge: edge extrapolation mode:

            - ``edge=1`` or ``edge='repeat'``: repeat edge, like Photoshop;
            - ``edge=2`` or ``edge='wrap'``: wrap around;
            - ``edge=``other: extrapolate with zeroes.
              Alpha=0 correspond to transparent.
        :param int | str method: interpolation method

            - ``method=2`` or ``method='barycentric'``: barycentric interpolation;
            - ``method=1`` or ``method='bilinear'``: bilinear interpolation.
        :return: rescaled image list, and ``maxcolors``.
        :rtype: tuple[list[list[list[int]]], int]

        .. note:: ``scale`` function, unlike ``rescale`` one, does not overwrite
            existing image but rather returns new one.

        """

        from .rescale import rescale as _rescale

        new_image_data = _rescale(self.image_data, width, height, edge, method)
        return (
            new_image_data,
            self.maxcolors,
        )  # WARNING: Gives extra tuple() when reading back, eliminated by __init__

    def displace(self, fx, fy, width: int, height: int, edge: int | str = 'repeat', method: int | str = 'bilinear'):
        """Image displacement according to ``fx`` and ``fy`` functions, using bilinear or barycentric interpolation depending on ``method`` switch.

        :param fx: actual x coordinate to read as a function of (x, y) requested;
        :type fx: callable[float, float]
        :param fy: actual y coordinate to read as a function of (x, y) requested;
        :type fy: callable[float, float]
        :param int width: resulting image width, pixels;
        :param int height: resulting image height, pixels;
        :param int | str edge: edge extrapolation mode:

            - ``edge=1`` or ``edge='repeat'``: repeat edge, like Photoshop;
            - ``edge=2`` or ``edge='wrap'``: wrap around;
            - ``edge=``other: extrapolate with zeroes.
              Alpha=0 correspond to transparent.
        :param int | str method: interpolation method

            - ``method=2`` or ``method='barycentric'``: barycentric interpolation;
            - ``method=1`` or ``method='bilinear'``: bilinear interpolation;
        :return: image, distorted according to ``fx``, ``fy`` rules, and ``maxcolors``.
        :rtype: tuple[list[list[list[int]]], int]

        """

        from .displace import displace as _displace

        new_image_data = _displace(self.image_data, fx, fy, width, height, edge, method)
        return (
            new_image_data,
            self.maxcolors,
        )

    def rotate(self, angle: float, edge: int | str = 'repeat', method: int | str = 'bilinear'):
        """Image rotation by means of displacement with algorithmic map, using bilinear or barycentric interpolation depending on ``method`` switch.

        :param float angle: rotation angle, degree counterclockwise;
        :param int | str edge: edge extrapolation mode:

            - ``edge=1`` or ``edge='repeat'``: repeat edge, like Photoshop;
            - ``edge=2`` or ``edge='wrap'``: wrap around;
            - ``edge=``other: extrapolate with zeroes.
              Alpha=0 correspond to transparent.
        :param int | str method: interpolation method

            - ``method=2`` or ``method='barycentric'``: barycentric interpolation;
            - ``method=1`` or ``method='bilinear'``: bilinear interpolation;
        :return: image, rotated by ``angle`` degrees counterclockwise, and ``maxcolors``.
        :rtype: tuple[list[list[list[int]]], int]

        """

        from math import cos, radians, sin

        from .displace import displace as _displace

        SIN = sin(radians(angle))
        COS = cos(radians(angle))

        width = int(abs(COS * self.X) + abs(SIN * self.Y))
        height = int(abs(SIN * self.X) + abs(COS * self.Y))

        def fx(x, y):
            return ((x - (width / 2)) * COS) - ((y - (height / 2)) * SIN) + (self.X / 2)

        def fy(x, y):
            return ((x - (width / 2)) * SIN) + ((y - (height / 2)) * COS) + (self.Y / 2)

        new_image_data = _displace(self.image_data, fx, fy, width, height, edge, method)
        return (
            new_image_data,
            self.maxcolors,
        )
