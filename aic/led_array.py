import wx
from aic import ActiveImageControl
from .util import dc_to_bitmap


class LedArray(ActiveImageControl):
    """
    An Active Image Control for presenting an array of two state (On / OFF) LED indicators,
    The bitmaps can be transparency masks or opaque
    If masks are used, set bg_colour for the colour you want for the LED
    :param bitmaps: An iterable containing two equal sized wx.Bitmap objects (bmp,bmp)
                    The  bitmap in (0) position represents the OFF state
                    The  bitmap in (1) position represents the ON state
    :param colour_list: an iterable of wx.colour objects - one for each element in the array
                        (ie for six LED elements, supply six colour objects)
    """

    def __init__(self, parent, bitmaps, colours=(wx.GREEN,), *args, **kwargs):
        super(LedArray, self).__init__(parent, *args, **kwargs)

        self.SetWindowStyleFlag(wx.NO_BORDER)

        self.parent = parent
        self.bmp_pair = bitmaps
        self.colours = colours
        self.vertical = True
        self.inverted = False
        self.bar = True       # True if bar style, False if point style
        self.bg_colour = wx.GREEN
        self.colour_shrink = 0  # reduce the rectangle on the back-painted solid colour (if used)
        self.stat_bmp = self.bmp_pair[0]
        self.stat_size = self.stat_bmp.Size
        self.elements = len(self.colours)
        self.spacing = 1
        self.stat_padding = (0, 0)
        self.stat_position = self.GetPosition() + self.stat_padding
        self._state = 0

        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_ENTER_WINDOW, lambda e: None)  # we can pass on this event
        self.Bind(wx.EVT_LEAVE_WINDOW, lambda e: None)  # ""

        # Class overrides #

    def DoGetBestSize(self):
        w, h = self.stat_size
        pad_x, pad_y = self.stat_padding
        spacing = self.spacing
        if self.vertical:
            size = wx.Size(w + pad_x * 2, ((h + spacing) * self.elements) - spacing + (pad_y * 2))  # for vertical
        else:
            size = wx.Size(((w + spacing) * self.elements) - spacing + pad_x * 2, h + pad_y * 2)  # for horizontal
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

        self.paint_array(context)

    # Instance methods #
    def paint_array(self, context):
        try:
            dc = wx.GCDC(context)
        except NotImplementedError:
            dc = context

        w, h = self.stat_size
        px, py = self.stat_padding

        for index, colour in enumerate(self.colours):
            if self.inverted:
                pen_col = brush_col = colour
            else:
                pen_col = brush_col = self.colours[-1 - index]

            dc.SetPen(wx.Pen(pen_col, width=1))
            dc.SetBrush(wx.Brush(brush_col))
            if self.vertical:
                sx, sy = (0, index * (h + self.spacing))  # vertical
            else:
                sx, sy = (index * (w + self.spacing), 0)  # horizontal
            x = px + sx
            y = py + sy
            rect = wx.Rect(x, y, w, h)

            # using Deflate to adjust rectangle size
            dc.DrawRectangle(rect.Deflate(self.colour_shrink))
            if self.bar:
                if self.inverted:
                    dc.DrawBitmap(self.bmp_pair[self.value > index], x, y)
                else:
                    dc.DrawBitmap(self.bmp_pair[self.value >= len(self.colours) - index], x, y)
            else:
                if self.inverted:
                    dc.DrawBitmap(self.bmp_pair[self.value == index+1], x, y)
                else:
                    dc.DrawBitmap(self.bmp_pair[self.value == len(self.colours) - index], x, y)

        bob = dc_to_bitmap(self, dc)
        # save_bmp_to_file(bob, 'bbits.png', filetype=wx.BITMAP_TYPE_PNG)
        return bob

    # Getters and Setters #
    def set_padding(self, padding):
        self.stat_padding = padding

    def set_style(self, is_bar_style=True):
        self.bar = is_bar_style

    def set_direction(self, is_reversed=False):
        self.bar = is_reversed

    # Properties #
    @property
    def value(self):
        return self._state

    @value.setter
    def value(self, state):
        if state != self._state:
            self._state = state
            self.parent.Refresh(True, self.GetRect())  # Refreshes the underlying portion of the background panel
