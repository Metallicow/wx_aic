import os
import wx
import wx.lib.inspection
from aic import ImageControlPanel, ImageControlFrame
from aic import SingleSlider
from aic.single_slider import EVT_SS_CHANGE

RESOURCES = 'res'


class ICPanel(ImageControlPanel):
    def __init__(self, parent, bmp, *args, tiled=False, **kwargs):
        super().__init__(parent, bmp, *args, tiled, **kwargs)

        self._populate()

        self.Bind(EVT_SS_CHANGE, self.on_slider_change, id=self.slide.GetId())

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
        slider_pair = (
            wx.Bitmap(os.path.join(RESOURCES, 'sticky_slide1.png')),
            wx.Bitmap(os.path.join(RESOURCES, 'sticky_slide1_handle.png')))
        self.slide = SingleSlider(self, slider_pair)
        self.slide.set_padding((30, 60))
        self.slide.set_offset((10,9))
        self.slide.set_default_pos((30, 0))
        self.slide.set_max((210, 0))
        self.slide.set_step(2, 4)
        self.slide.set_highlighting()
        self.slide.highlight_box = ((0, 0), (20, 40))
        mid_sizer.Add(self.slide, 0, 0, 10)

        mid_sizer.Add((0, 0), 1, wx.EXPAND, 5)

        bot_sizer = wx.BoxSizer(wx.HORIZONTAL)
        bot_sizer.Add((0, 0), 1, wx.EXPAND, 5)
        bot_sizer.Add((0, 0), 1, wx.EXPAND, 5)

        panel_sizer.Add(top_sizer, 1, wx.EXPAND, 5)
        panel_sizer.Add(mid_sizer, 1, wx.EXPAND, 5)
        panel_sizer.Add(bot_sizer, 1, wx.EXPAND, 5)

        self.SetSizer(panel_sizer)
        self.Layout()

    def on_slider_change(self,event):
        self.Text1.SetLabel(str(int(event.state*100)))
        event.Skip()

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
        self.Text1 = wx.StaticText(self, wx.ID_ANY, "Static Text", wx.DefaultPosition, wx.DefaultSize, 0)
        top_sizer.Add(self.Text1, 0, wx.ALL, 10)
        top_sizer.Add((0, 0), 1, wx.EXPAND, 5)
        mid_sizer = wx.BoxSizer(wx.HORIZONTAL)
        mid_sizer.Add((0, 0), 1, wx.EXPAND, 5)

        # Add a rotary dial control #
        slider_pair = (
            wx.Bitmap(os.path.join(RESOURCES, 'sticky_knob1.png')),
            wx.Bitmap(os.path.join(RESOURCES, 'sticky_knob1_mark.png')))
        self.slider = SingleSlider(self, slider_pair)
        mid_sizer.Add(self.slider,0,0, 10)

        mid_sizer.Add((0, 0), 1, wx.EXPAND, 5)
        bot_sizer = wx.BoxSizer(wx.HORIZONTAL)
        bot_sizer.Add((0, 0), 1, wx.EXPAND, 5)
        bot_sizer.Add((0, 0), 1, wx.EXPAND, 5)

        panel_sizer.Add(top_sizer, 1, wx.EXPAND, 5)
        panel_sizer.Add(mid_sizer, 1, wx.EXPAND, 5)
        panel_sizer.Add(bot_sizer, 1, wx.EXPAND, 5)

        self.SetSizer(panel_sizer)
        self.Layout()

        self.Bind(EVT_SS_CHANGE, self.on_dial_change, id=self.dial.GetId())

    def on_dial_change(self,event):
        self.Text1.SetLabel(str(event.state))
        event.Skip()

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
