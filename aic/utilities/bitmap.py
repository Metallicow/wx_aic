# bitmap.py

import wx

__all__ = ['dc_to_bitmap', 'save_bmp_to_file']


def save_bmp_to_file(bmp, filepath, filetype=wx.BITMAP_TYPE_PNG):
    """ Helper method to save a copy of a bitmap to file; primarily for debugging / testing """
    img = bmp.ConvertToImage()
    img.SaveFile(filepath, filetype)


def dc_to_bitmap(window, background_dc):
    """ returns the contents of a dc as a bitmap """
    width, height = window.GetClientSize()
    bitmap = wx.Bitmap(width, height)

    dc = wx.MemoryDC(bitmap)
    dc.Blit(0, 0, width, height, background_dc, 0, 0)
    dc.SelectObject(wx.NullBitmap)
    return bitmap
