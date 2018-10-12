import wx
from .utilities import dc_to_bitmap


class ImageControlPanel(wx.Panel):
    """
    Displays a background image (which can be tiled)
    """

    def __init__(self, parent, bg_bitmap, tiled=False, *args, **kw):
        super().__init__(parent, *args, **kw)
        self.parent = parent
        self.bg_bitmap = bg_bitmap
        self.bg_width = self.bg_bitmap.Size.width
        self.bg_height = self.bg_bitmap.Size.height
        self.tiled_bg = tiled

        self.bg_render = self.bg_bitmap  # initially instantiated with the background image

        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_SIZE, self.on_size)

    def on_size(self, event):
        self.parent.Refresh()
        event.Skip()  # this is important

    def on_paint(self, _):
        x = y = 0
        dc = wx.AutoBufferedPaintDC(self)  # wx.PaintDC(self)

        # Draw the background, tiling the image if requested but ONLY IF client size has changed...
        # otherwise draw the background using self.bg_render.
        if self.bg_render.GetSize() != self.GetClientSize():

            if self.tiled_bg:
                w, h = self.GetSize()
                cols = (w // self.bg_width) + 1
                rows = (h // self.bg_height) + 1
                # print('tiled Panel painting')
                for r in range(rows):
                    for c in range(cols):
                        dc.DrawBitmap(self.bg_bitmap, x, y)
                        x += self.bg_width
                    y += self.bg_height
                    x = 0
            else:
                # print('non-tiled Panel painting')
                dc.DrawBitmap(self.bg_bitmap, x, y)

            self.bg_render = dc_to_bitmap(self, dc)  # Retain the now-rendered background locally

        else:
            # print('drawing Panel background from previous render')
            dc.DrawBitmap(self.bg_render, x, y)
