import wx
from aic import ActiveImageControl


class LedSingle(ActiveImageControl):
    """
    An Active Image Control for presenting a two state (On / OFF) LED indicator
    The bitmaps can be transparency masks or opaque
    If masks are used, set bg_colour for the colour you want for the LED
    :param bitmaps: An iterable containing two equally dimensioned wx.Bitmap objects (bmp,bmp)
                    The  bitmap in (0) position represents the OFF state
                    The  bitmap in (1) position represents the ON state
    """

    def __init__(self, parent, bitmaps, *args, **kwargs):
        super(LedSingle, self).__init__(parent, *args, **kwargs)

        self.SetWindowStyleFlag(wx.NO_BORDER)

        self.parent = parent
        self.bmp_pair = bitmaps
        # self.orientation = 0  # 0 for vertical, 1 for horizontal
        self.bg_colour = wx.GREEN
        self.colour_shrink = 0  # reduce the rectangle on the back-painted solid colour (if used)
        self.stat_bmp = self.bmp_pair[0]
        self.stat_size = self.stat_bmp.Size
        self.stat_padding = (0, 0)
        self.stat_position = self.GetPosition() + self.stat_padding    # TODO remove if not used
        self.stat_rect = wx.Rect(self.stat_position, self.stat_size)    # TODO remove if not used
        self._state = False

        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_ENTER_WINDOW, lambda e: None)  # the led displays are not interactive
        self.Bind(wx.EVT_LEAVE_WINDOW, lambda e: None)  # so we can pass on these events

    # Class overrides #
    def DoGetBestSize(self):
        w, h = self.stat_size
        pad_x, pad_y = self.stat_padding
        size = wx.Size(w + pad_x * 2, h + pad_y * 2)
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
        window_rect = self.GetRect()
        buffer_bitmap = self.parent.bg_render.GetSubBitmap(window_rect)
        context = wx.BufferedPaintDC(self, buffer_bitmap)

        self.paint_single(context)

    # instance methods #

    def paint_single(self, context):

        try:
            dc = wx.GCDC(context)
        except NotImplementedError:
            dc = context

        pen_col = brush_col = self.bg_colour
        dc.SetPen(wx.Pen(pen_col, width=1))
        dc.SetBrush(wx.Brush(brush_col))
        rect = wx.Rect(self.stat_padding, self.stat_size)

        # using Deflate to correct for the extra line width added by DrawRectangle
        dc.DrawRectangle(rect.Deflate(self.colour_shrink))
        dc.DrawBitmap(self.stat_bmp, self.stat_padding)

    def toggle_state(self):
        self._state = not self._state
        self.stat_bmp = self.bmp_pair[self._state]

        self.parent.Refresh(True, self.GetRect())  # Refreshes the underlying portion of the background panel

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
            self.toggle_state()
