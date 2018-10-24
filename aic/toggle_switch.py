import wx
from wx.lib.newevent import NewCommandEvent
from aic import ActiveImageControl

ts_cmd_event, EVT_TS_CHANGE = NewCommandEvent()


class ToggleSwitch(ActiveImageControl):
    def __init__(self, parent, bitmaps, *args, **kwargs):
        """
        An Active Image Control for presenting a two position ON/OFF switch style

        :param bitmaps: An iterable containing two equal sized wx.Bitmap objects (bmp,bmp)
                        The  bitmap in (0) position is treated as the default (OFF) base bitmap
        """
        # TODO option to rebind mouse to different functions eg wx.EVT_RIGHT_UP  to toggle state?
        super().__init__(parent, *args, **kwargs)

        self.SetWindowStyleFlag(wx.NO_BORDER | wx.WANTS_CHARS)

        self.parent = parent
        self.bmp_pair = bitmaps
        self.stat_bmp = self.bmp_pair[0]
        self.stat_size = self.stat_bmp.Size
        self.stat_padding = (0, 0)

        self._state = False

        # self.highlight_box = ((0, 0), (0, 0))

        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.Bind(wx.EVT_PAINT, self.on_paint)

        # self.Bind(AIC_TS_CHANGE, self.on_cust_event)

        self.Bind(wx.EVT_KEY_DOWN, self.on_keypress)
        self.Bind(wx.EVT_LEFT_DOWN, self.on_left_down)
        self.Bind(wx.EVT_LEFT_DCLICK, self.on_left_down)

    # Class overrides #
    def DoGetBestSize(self):
        w, h = self.stat_size
        pad_x, pad_y = self.stat_padding
        size = wx.Size(w + pad_x * 2, h + pad_y * 2)
        return size

    # Event Handling #
    def on_paint(self, _):
        window_rect = self.GetRect()
        buffer_bitmap = self.parent.bg_render.GetSubBitmap(window_rect)
        dc = wx.BufferedPaintDC(self, buffer_bitmap)
        dc.DrawBitmap(self.stat_bmp, self.stat_padding)

        if self.highlight and self.HasFocus():
            self.draw_highlight(dc, ((0, 0), (4, 4)))

    def on_keypress(self, event):
        if self.HasFocus():
            keycode = event.GetKeyCode()
            if keycode == wx.WXK_SPACE:
                self.toggle_state()
            elif keycode == wx.WXK_TAB:
                self.Navigate(not (event.ShiftDown()))  # Navigates backwards if 'shift' key is held
        event.Skip()

    def on_left_down(self, _):
        # self._primed = True
        if not self.HasFocus():
            self.SetFocus()
        self.toggle_state()

    # instance methods
    def toggle_state(self):
        self._state = not self._state
        self.stat_bmp = self.bmp_pair[self._state]

        self.parent.Refresh(True, self.GetRect())  # Refreshes the underlying portion of the background panel
        wx.PostEvent(self, ts_cmd_event(id=self.GetId(), state=self._state))

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
