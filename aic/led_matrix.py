import time     # todo remove - purely for checking / testing draw times
import wx
from aic import ActiveImageControl


class LedMatrix(ActiveImageControl):
    """
    An Active Image Control for presenting a matrix of two state (On / OFF) LED indicators
    The bitmaps can be transparency masks or opaque
    If masks are used, set bg_colour for the colour you want for the LEDs

    :param bitmaps: An iterable containing two equally dimensioned wx.Bitmap objects
                    The  bitmap in (0) position represents the OFF state
                    The  bitmap in (1) position represents the ON state
    :param dimension:   A tuple with the number of elements needed ( rows, columns)

    Note: The whole matrix is redrawn, every time, in one hit - quite fast for a large number of elements
    """

    def __init__(self, parent, bitmaps, dimension=(1, 1), *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self.SetWindowStyleFlag(wx.NO_BORDER)

        self.parent = parent
        self.bmp_pair = bitmaps
        self.rows, self.columns = dimension
        # self.orientation = 0  # 0 for vertical, 1 for horizontal
        self.bg_colour = wx.GREEN
        self.colour_shrink = 0  # reduce the rectangle on the back-painted solid colour (if used)
        self.stat_bmp = self.bmp_pair[0]
        self.stat_size = self.stat_bmp.Size
        self.stat_padding = (0, 0)
        self.spacing = 1
        self.stat_position = self.GetPosition() + self.stat_padding  # Top left corner of matrix (inside of any padding)
        self.stat_rect = wx.Rect(self.stat_position, self.stat_size)  # Matrix  excluding padding TODO size ? Needed?
        self._state = [0] * self.columns  # TODO two dimensional array? each column has a value

        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_ENTER_WINDOW, lambda e: None)  # we can pass on this event
        self.Bind(wx.EVT_LEAVE_WINDOW, lambda e: None)  # ""

    # Class overrides #
    def DoGetBestSize(self):
        w, h = self.stat_size
        pad_x, pad_y = self.stat_padding
        space = self.spacing
        size = wx.Size(((w + space) * self.columns) + (pad_x * 2),
                       ((h + space) * self.rows) + (pad_y * 2))
        return size

    def AcceptsFocusFromKeyboard(self):
        """ Overridden base class """
        # We don't want focus from keyboard
        return False

    def AcceptsFocus(self):
        """ Overridden base class """
        # We don't want focus from the mouse either
        return False

    # Event Handling #
    def on_paint(self, _):
        start = time.perf_counter()
        window_rect = self.GetRect()
        buffer_bitmap = self.parent.bg_render.GetSubBitmap(window_rect)  # the bit of panel bitmap we draw on

        context = wx.BufferedPaintDC(self, buffer_bitmap)

        self.paint_matrix(context)
        print(time.perf_counter() - start)
        # on screen painting only occurs the instance that this method exits

    # instance methods #
    def paint_matrix(self, context):

        try:
            dc = wx.GCDC(context)
        except NotImplementedError:
            dc = context

        pen_col = brush_col = self.bg_colour
        dc.SetPen(wx.Pen(pen_col, width=1))
        dc.SetBrush(wx.Brush(brush_col))

        px, py = self.stat_padding
        w, h = self.stat_bmp.Size

        for column in range(self.columns):
            for row in range(self.rows):
                point = px + (column * (w + self.spacing)), py + (row * (h + self.spacing))
                rect = wx.Rect(point, self.stat_size)

                col_val = self.value[column]
                # using Deflate to correct for the extra line width added by DrawRectangle
                # if col_val >= self.rows - row:    # Use this method if only drawing rects (not bmps)
                #     dc.DrawRectangle(rect.Deflate(self.colour_shrink))
                dc.DrawRectangle(rect.Deflate(self.colour_shrink))
                dc.DrawBitmap(self.bmp_pair[col_val >= self.rows - row], point)

    # Getters and Setters #
    def set_padding(self, padding):
        self.stat_padding = padding

    # Properties #
    @property
    def value(self):
        return self._state

    @value.setter
    def value(self, state):
        if state != self._state:
            self._state = state
            self.parent.Refresh(True, self.GetRect())

