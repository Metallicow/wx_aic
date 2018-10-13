import os
import wx
from aic import ImageControlPanel, ImageControlFrame
from aic import RotaryDial

RESOURCES = 'res'


class ICPanel(ImageControlPanel):
    def __init__(self, parent, bmp, *args, tiled=False, **kwargs):
        super().__init__(parent, bmp, *args, tiled, **kwargs)

        self._populate()

    def _populate(self):
        panel_sizer = wx.BoxSizer(wx.VERTICAL)

        top_sizer = wx.BoxSizer(wx.HORIZONTAL)
        top_sizer.Add((0, 0), 1, wx.EXPAND, 5)
        self.Text1 = wx.StaticText(self, wx.ID_ANY, "Static Text", wx.DefaultPosition, wx.DefaultSize, 0)
        top_sizer.Add(self.Text1, 0, wx.ALL, 10)
        top_sizer.Add((0, 0), 1, wx.EXPAND, 5)

        mid_sizer = wx.BoxSizer(wx.HORIZONTAL)
        mid_sizer.Add((0, 0), 1, wx.EXPAND, 5)

        # Add a rotary dial control #
        dial_pair = (
            wx.Bitmap(os.path.join(RESOURCES, 'sticky_knob1.png')),
            wx.Bitmap(os.path.join(RESOURCES, 'sticky_knob1_mark.png')))
        self.dial = RotaryDial(self, dial_pair, style=wx.WANTS_CHARS)  # TODO wantchars should be in the dial class?
        self.dial.set_padding((10, 10))
        self.dial.highlight_box = ((10,10), (3,3))
        self.dial.set_rotation_point_offset((-1, 0))
        self.dial.set_zero_angle_offset(-225)
        self.dial.set_pointer_rot_offset(-135)
        self.dial.set_initial_angle(0)
        self.dial.set_max_angle(270)
        self.dial.set_step(2, 4)
        self.dial.set_highlighting()
        mid_sizer.Add(self.dial,0,0, 10)

        mid_sizer.Add((0, 0), 1, wx.EXPAND, 5)

        bot_sizer = wx.BoxSizer(wx.HORIZONTAL)
        bot_sizer.Add((0, 0), 1, wx.EXPAND, 5)
        bot_sizer.Add((0, 0), 1, wx.EXPAND, 5)

        panel_sizer.Add(top_sizer, 1, wx.EXPAND, 5)
        panel_sizer.Add(mid_sizer, 1, wx.EXPAND, 5)
        panel_sizer.Add(bot_sizer, 1, wx.EXPAND, 5)

        self.SetSizer(panel_sizer)
        self.Layout()

    def __del__(self):
        pass


class StdPanel(wx.Panel):

    def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition, size=wx.Size(1024, 768), style=wx.TAB_TRAVERSAL,
                 name=wx.EmptyString):
        super().__init__(parent, id=id, pos=pos, size=size, style=style, name=name)

        self._populate()

    def _populate(self):
        panel_sizer = wx.BoxSizer(wx.VERTICAL)

        top_sizer = wx.BoxSizer(wx.HORIZONTAL)
        top_sizer.Add((0, 0), 1, wx.EXPAND, 5)
        top_sizer.Add((0, 0), 1, wx.EXPAND, 5)
        mid_sizer = wx.BoxSizer(wx.HORIZONTAL)
        mid_sizer.Add((0, 0), 1, wx.EXPAND, 5)
        mid_sizer.Add((0, 0), 1, wx.EXPAND, 5)
        bot_sizer = wx.BoxSizer(wx.HORIZONTAL)
        bot_sizer.Add((0, 0), 1, wx.EXPAND, 5)
        bot_sizer.Add((0, 0), 1, wx.EXPAND, 5)

        panel_sizer.Add(top_sizer, 1, wx.EXPAND, 5)
        panel_sizer.Add(mid_sizer, 1, wx.EXPAND, 5)
        panel_sizer.Add(bot_sizer, 1, wx.EXPAND, 5)

        self.SetSizer(panel_sizer)
        self.Layout()

    def __del__(self):
        pass


class StdFrame(wx.Frame):

    def __init__(self, parent):
        super().__init__(parent, id=wx.ID_ANY, title="Example wxFrame", pos=wx.DefaultPosition, size=wx.Size(1024, 768),
                         style=wx.DEFAULT_FRAME_STYLE | wx.TAB_TRAVERSAL)
        # self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)

        frame_sizer = wx.BoxSizer(wx.HORIZONTAL)

        """ Choose a panel """
        # self.main_panel = StdPanel(self)
        panel_bmp = wx.Bitmap(os.path.join(RESOURCES, 'sticky_bg.png'))
        self.main_panel = ICPanel(self, panel_bmp, tiled=True)

        """ Optional second panel """
        # # self.main_panel2 = StdPanel(self)
        # panel_bmp = wx.Bitmap(os.path.join(RES, 'sticky_bg.png'))
        # self.main_panel2 = ICPanel(self, panel_bmp, tiled=True)

        frame_sizer.Add(self.main_panel, 1, wx.EXPAND, 5)
        # frame_sizer.Add(self.main_panel2, 1, wx.EXPAND, 5)

        self.SetSizer(frame_sizer)
        self.Layout()
        self.Centre(wx.BOTH)

        self.Bind(wx.EVT_CLOSE, self.on_close)

    def __del__(self):
        pass

    def on_close(self, event):
        pass
        event.Skip()


class ICFrame(ImageControlFrame):
    bmp = (os.path.join(RESOURCES, 'led1rect_active_dark.png'))

    def __init__(self, parent, resizable=True, bitmap=bmp, tiled=True):
        super().__init__(parent, resizable=resizable, bitmap=bitmap, tiled=tiled, id=wx.ID_ANY, title="Example ICFrame",
                         pos=wx.DefaultPosition, size=wx.Size(1024, 768), style=wx.DEFAULT_FRAME_STYLE)
        # self.SetSizeHints(wx.Size(1024, 768), wx.DefaultSize, wx.DefaultSize)  # Minimum size

        # self.SetTransparent(125)
        # self.set_background(wx.Bitmap(os.path.join(RES, 'led1rect_active_dark.png')))
        # self.set_tiled(True)
        # self.set_stored(True)

        frame_sizer = wx.BoxSizer(wx.HORIZONTAL)

        """ Choose a panel """
        # self.main_panel = StdPanel(self)
        panel_bmp = wx.Bitmap(os.path.join(RESOURCES, 'sticky_bg.png'))
        self.main_panel = ICPanel(self, panel_bmp, tiled=True)

        """ Optional second panel """
        # self.main_panel2 = StdPanel(self)
        # panel_bmp = wx.Bitmap(os.path.join(RES, 'sticky_bg.png'))
        # # self.main_panel2 = ICPanel(self, panel_bmp, tiled=True)

        frame_sizer.Add(self.main_panel, 1, wx.EXPAND, 5)
        # frame_sizer.Add(self.main_panel2, 1, wx.EXPAND, 5)

        self.SetSizer(frame_sizer)
        self.Layout()
        self.Centre(wx.BOTH)

        self.Bind(wx.EVT_CLOSE, self.on_close)

    def on_close(self, event):
        pass
        event.Skip()


def main():
    app = wx.App(False)
    # wx.lib.inspection.InspectionTool().Show()

    """ Choose a frame """
    # mainframe = StdFrame(None)
    mainframe = ICFrame(None)

    mainframe.Show()
    app.MainLoop()


if __name__ == '__main__':
    main()
