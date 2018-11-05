import wx
from .util import dc_to_bitmap


class ImageControlPanel(wx.Panel):
    """
    Build a Panel with a background image, tiling the image if requested
    If the image has alpha values, the window below the Panel will appear to show through
    """

    def __init__(self, parent, bg_bitmap, tiled=False, *args, **kw):
        super(ImageControlPanel, self).__init__(parent, *args, **kw)
        self.parent = parent
        self.bg_bitmap = bg_bitmap
        self.tiled_bg = tiled
        self.bg_render = self.bg_bitmap  # instantiated with the passed background image

        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_SIZE, self.on_size)

    def on_size(self, event):
        self.parent.Refresh()
        event.Skip()  # propagation is important

    def on_paint(self, _):
        x = y = 0
        dc = wx.AutoBufferedPaintDC(self)  # wx.PaintDC(self)

        # Draw the background, tiling the image if requested but ONLY IF client size has changed...
        # otherwise draw the background using previously rendered bitmap (self.bg_render)
        if self.bg_render.GetSize() != self.GetClientSize():

            if self.tiled_bg:
                w, h = self.GetSize()
                bg_w = self.bg_bitmap.GetWidth()
                bg_h = self.bg_bitmap.GetHeight()
                cols = (w // bg_w) + 1
                rows = (h // bg_h) + 1
                # print('tiled Panel painting')
                for r in range(rows):
                    for c in range(cols):
                        dc.DrawBitmap(self.bg_bitmap, x, y)
                        x += bg_w
                    y += bg_h
                    x = 0
            else:
                # print('non-tiled Panel painting')
                dc.DrawBitmap(self.bg_bitmap, x, y)

            self.bg_render = dc_to_bitmap(self, dc)  # Retain the now-rendered background

        else:
            # print('drawing Panel background from previous render')
            dc.DrawBitmap(self.bg_render, x, y)
