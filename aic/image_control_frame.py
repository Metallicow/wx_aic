import wx
from .utilities import dc_to_bitmap


class ImageControlFrame(wx.Frame):
    """
    Build a Frame with a background image, tiling the image if requested
    If an image with an alpha value is used, the frame's BackgroundColour will show through
    """

    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.SetBackgroundColour(wx.BLACK)

        self._bg_bitmap = wx.EmptyBitmap
        self._bg_width = 0
        self._bg_height = 0
        self.tiled_bg = False
        self._bg_render = self._bg_bitmap

        # Setting to True is only useful if you are drawing other objects directly onto the Frame - ie. not using Panels
        self.store_render = False

        self.Bind(wx.EVT_ERASE_BACKGROUND, self._on_erase_background)
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.Bind(wx.EVT_PAINT, self.on_paint)

    def _on_erase_background(self, _):
        pass

    def on_paint(self, _):
        x, y = 0, 0
        w, h = self.GetSize()

        # Using Auto/BufferedPaintDC prevents corruption
        dc = wx.AutoBufferedPaintDC(self)

        # Draw a background rectangle to prevent corruption, when using images that have transparency
        if self._bg_bitmap.ConvertToImage().HasAlpha():
            brush = dc.GetBrush()
            brush.SetColour(dc.GetTextBackground())
            dc.SetBrush(brush)
            dc.DrawRectangle(x, y, w, h)

        # If client size has changed, draw the bg_bitmap, tiling the bitmap if requested
        # If size is unchanged, draw the background using self.bg_render.
        if self._bg_render.GetSize() != self.GetClientSize():

            if self.tiled_bg:
                # Tiled bitmap drawn to Frame
                columns = (w // self._bg_width) + 1
                rows = (h // self._bg_height) + 1
                for row in range(rows):
                    for col in range(columns):
                        dc.DrawBitmap(self._bg_bitmap, x, y)
                        x += self._bg_width
                    y += self._bg_height
                    x = 0
            else:
                # Single bitmap drawn to Frame
                dc.DrawBitmap(self._bg_bitmap, x, y)

            if self.store_render:
                # Stores the last drawn bitmap
                self._bg_render = dc_to_bitmap(self, dc)

        else:
            # Draw the previously saved bitmap to Frame
            dc.DrawBitmap(self._bg_render, x, y)

    def set_background(self, bg_bitmap, tiled=False, stored=False):
        self._bg_bitmap = bg_bitmap
        self._bg_width = self._bg_bitmap.Size.width
        self._bg_height = self._bg_bitmap.Size.height
        self._bg_render = self._bg_bitmap
        self.set_tiled(tiled)
        self.set_stored(stored)

    def set_tiled(self, tiled=True):
        self.tiled_bg = tiled

    def set_stored(self, stored=True):
        self.store_render = stored
