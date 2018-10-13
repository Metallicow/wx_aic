import wx


class ActiveImageControl(wx.Control):
    """ A sub-classed Control utilising images to behave as controls """

    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self.highlight = False

        self.Bind(wx.EVT_ERASE_BACKGROUND, self._on_erase_background)
        self.Bind(wx.EVT_SET_FOCUS, self._on_focus_change)
        self.Bind(wx.EVT_KILL_FOCUS, self._on_focus_change)

    def _on_erase_background(self, _):
        pass

    def _on_focus_change(self, event):
        self.Refresh()
        event.Skip()

    # TODO make highlight an object that can be attached to any window, each with it's own parameters
    def draw_highlight(self, context, size, adjustment):
        """ Draw a highlighting square around the control """
        try:
            dc = wx.GCDC(context)
        except NotImplementedError:
            dc = context

        offset = adjustment[0]
        sizing = adjustment[1]
        c_r, c_g, c_b, c_a = wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHT)
        for RGBA, width, i_offset, rect, cnr_rad in [
            # ((40, 255, 40, 28), 2, (0, 0), self.Rect.Deflate(sizing), 8),
            # ((35, 142, 35, 10), 3, (1, 1), self.Rect.Deflate(sizing[0] + 1, sizing[1] + 1), 8),
            # ((0, 22, 0, 88), 1, (2, 2), self.Rect.Deflate(sizing[0] + 2, sizing[1] + 2), 8)
            ((c_r, c_g, c_b, c_a - 155), 1, (0, 0), wx.Rect((0, 0), size).Deflate(sizing), 4),
            ((c_r, c_g, c_b, c_a - 200), 1, (1, 1), wx.Rect((0, 0), size).Deflate(sizing[0] + 1, sizing[1] + 1), 4)
        ]:
            r, g, b, a = RGBA
            pen_col = wx.Colour(r, g, b, a)
            brush_col = wx.TRANSPARENT_BRUSH
            dc.SetPen(wx.Pen(pen_col, width=width))
            dc.SetBrush(wx.Brush(brush_col))
            rect.SetPosition(wx.Point(offset) + wx.Point(i_offset) + wx.Point(sizing))
            dc.DrawRoundedRectangle(rect, cnr_rad)

    def set_highlighting(self, highlight=True):
        self.highlight = highlight
