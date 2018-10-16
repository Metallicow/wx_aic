import time
from math import atan2, pi, degrees, radians

import wx
from wx.lib.newevent import NewCommandEvent
import pytweening as ptw

from aic import ActiveImageControl

rd_cmd_event, EVT_RD_CHANGE = NewCommandEvent()


class RotaryDial(ActiveImageControl):

    def __init__(self, parent, bitmaps, *args, **kwargs):
        """
        An Image Control for presenting a rotary dial style, (eg a knob or dial type control)
        It behaves similarly to a native control slider, except value is expressed as degrees (float)

        :param bitmaps:  wx.BitMap objects - iterable
                        (first bitmap will be the static background)
                        (the second will be the dynamic pointer - an bitmap suitable for rotation - eg a knob pointer)
                        NB: The dynamic bitmap MUST BE A SQUARE (w=h);
                        Even pixel dimensions will rotate slightly better (eg 50x50 not 51x51)
                        The rotating bitmap must be smaller than the base bitmap
                        It might be possible to do a partially exposed knob using a mask???
        """

        super().__init__(parent, *args, **kwargs)
        # No borders, yuk!  Wants Chars - to grab (cursor) key input
        self.SetWindowStyleFlag(wx.NO_BORDER | wx.WANTS_CHARS)

        self.parent = parent
        self.stat_bmp = bitmaps[0]
        self._stat_size = self.stat_bmp.Size
        # self.stat_width = self.stat_bmp.Size.width   # not needed?
        # self.stat_height = self.stat_bmp.Size.height   # not needed?
        self._stat_centre = rect_centre(self._stat_size)
        self.stat_padding = (0, 0)
        self._stat_position = self.GetPosition() + self.stat_padding
        # self.stat_rect = wx.Rect(self.stat_position, self.stat_size)   # not needed?

        self.stat_rot_pnt_offset = (0, 0)  # the offset for the centre point that dynam_bmp will rotate around
        self.stat_rot_pnt_centre = (self._stat_position + self._stat_centre + self.stat_rot_pnt_offset)

        self.dynam_bmp = bitmaps[1]
        self._dynam_size = self.dynam_bmp.Size
        self._dynam_centre = rect_centre(self._dynam_size)
        self._dynam_pos = self.stat_rot_pnt_centre - self._dynam_centre
        # degrees rotation to make pointer align with minimum position (-ve for counter-clockwise; +ve for clockwise)
        self._dynam_bmp_rot_offset = -135

        # degrees of rotation from the 3 o'clock position to the minimum limit of the dial ie (the zero position)
        self._zero_angle_offset = 0
        self._scroll_step = 1
        self._key_step = 1
        self.pointer_default = 50
        self._pointer_min_angle = 0
        self.pointer_max_angle = 360
        self._pointer_limit_hit = None
        self._pointer_angle = self.pointer_default

        self.highlight_box = ((0, 0), (0, 0))

        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.Bind(wx.EVT_PAINT, self.on_paint)

        self.Bind(wx.EVT_KEY_DOWN, self.on_keypress)
        self.Bind(wx.EVT_LEFT_DOWN, self.on_left_down)
        self.Bind(wx.EVT_MIDDLE_UP, self.on_middle_up)
        self.Bind(wx.EVT_MOUSEWHEEL, self.on_mouse_wheel)
        self.Bind(wx.EVT_MOUSE_EVENTS, self.on_left_drag)

    # Class overrides #
    def DoGetBestSize(self):
        w, h = self._stat_size
        pad_x, pad_y = self.stat_padding
        size = wx.Size(w + pad_x * 2, h + pad_y * 2)
        return size

    # Event handling #
    def on_paint(self, _):
        window_rect = self.GetRect()
        buffer_bitmap = self.parent.bg_render.GetSubBitmap(window_rect)
        self.draw_to_context(wx.BufferedPaintDC(self, buffer_bitmap))

    def draw_to_context(self, dc):
        dc.DrawBitmap(self.stat_bmp, self._stat_position)
        indicator_angle = self._parse_angle(360 - self._pointer_angle - self._dynam_bmp_rot_offset)
        indicator = self.rotate_bmp(self.dynam_bmp, indicator_angle)
        dc.DrawBitmap(indicator, self._dynam_pos)

        if self.highlight and self.HasFocus():
            self.draw_highlight(dc, self.GetSize(), self.highlight_box)

    def on_keypress(self, event):
        if self.HasFocus():
            keycode = event.GetKeyCode()
            if keycode in [wx.WXK_RIGHT, wx.WXK_UP]:
                self.set_angle(self._pointer_angle + self._key_step)
            elif keycode in [wx.WXK_LEFT, wx.WXK_DOWN]:
                self.set_angle(self._pointer_angle - self._key_step)
            elif keycode == wx.WXK_SPACE:
                self._animated_reset()
            elif keycode == wx.WXK_TAB:
                self.Navigate(not (event.ShiftDown()))  # Navigates backwards if 'shift' key is held
        event.Skip()

    def on_left_down(self, event):
        if not self.HasFocus():
            self.SetFocus()
        mouse_pos = event.GetPosition()
        mouse_angle = angle_diff(mouse_pos, self.stat_rot_pnt_centre)
        mouse_angle_offset = mouse_angle - self._zero_angle_offset
        self.set_angle(mouse_angle_offset)

    def on_left_drag(self, event):
        if event.Dragging() and event.LeftIsDown():
            if not self.HasFocus():
                self.SetFocus()
            mouse_pos = event.GetPosition()
            mouse_angle = angle_diff(mouse_pos, self.stat_rot_pnt_centre)
            mouse_angle_offset = mouse_angle - self._zero_angle_offset
            self.set_angle(mouse_angle_offset)
        event.Skip()

    def on_middle_up(self, _):
        if not self.HasFocus():
            self.SetFocus()
        self._animated_reset()

    def on_mouse_wheel(self, event):
        if not self.HasFocus():
            self.SetFocus()
        delta = event.GetWheelDelta()  # usually +/-120, but it's better not to assume
        angle = self._pointer_angle + (self._scroll_step * event.GetWheelRotation() // delta)
        self.set_angle(angle)

    # Getters and Setters #
    def set_padding(self, padding=(0, 0)):
        """ Apply additional padding around the static image, mouse events will extend into the padding """
        self.stat_padding = padding
        self._update_params()

    def set_rotation_point_offset(self, offset=(0, 0)):
        """ Apply a correctional offset to the point that the dynamic image will revolve around
             offset is a valid wx.Point
        """
        self.stat_rot_pnt_offset = offset
        self._update_params()

    def set_pointer_rot_offset(self, angle=0.0):
        """ Apply a rotational offset to the dynamic image ( -ve for ccw; +ve for cw )
            angle is the degrees of rotation needed to align the pointer with the zero position
        """
        self._dynam_bmp_rot_offset = self._parse_angle(angle)
        self._refresh()

    def set_zero_angle_offset(self, angle=0.0):
        self._zero_angle_offset = self._parse_angle(angle)

    def set_initial_angle(self, angle=0.0):
        """ Set the default angle (in degrees) for the pointer, resetting will place the pointer at this angle"""
        self.set_angle(angle)
        self.pointer_default = self._pointer_angle

    def set_max_angle(self, angle=360.0):
        self.pointer_max_angle = self._parse_angle(angle)
        if self._pointer_angle > self.pointer_max_angle:
            self.set_angle(self._pointer_angle)

    def set_step(self, scroll=1.0, key=1.0):
        """ Set the increment value (in degrees) for the scroll-wheel and cursor keys"""
        self.set_scroll_step(scroll)
        self.set_key_step(key)

    def set_scroll_step(self, step=1.0):
        """ Set the scroll-wheel step size in degrees (float > 0) """
        self._scroll_step = step

    def set_key_step(self, step=1.0):
        """ Set the key step size in degrees (float > 0) """
        self._key_step = step

    def set_angle(self, angle=0.0):
        """ Set the rotational position of the dynamic image via an angle value """
        angle_ = self._parse_angle(angle)
        if angle != self._pointer_angle:
            self._pointer_angle = self._parse_limits(angle_, self.pointer_max_angle)
            wx.PostEvent(self, rd_cmd_event(id=self.GetId(), state=self._pointer_angle))
            self._refresh()

    def reset(self, animate=True):
        self._animated_reset(animate)

    # Properties #
    @property
    def value(self):
        return self._pointer_angle

    @value.setter
    def value(self, angle):
        self.set_angle(angle)

    # Helper methods #
    def _update_params(self):
        self._stat_position = self.GetPosition() + self.stat_padding
        # self.stat_rect = wx.Rect(self._stat_position, self._stat_size)  # not needed?
        self.stat_rot_pnt_centre = (self._stat_position + self._stat_centre + self.stat_rot_pnt_offset)
        self._dynam_pos = self.stat_rot_pnt_centre - self._dynam_centre

    def _refresh(self):
        self.Refresh(True, (wx.Rect(self._dynam_pos, self._dynam_size)))

    def _animated_reset(self, animate=True):
        if not animate:
            self.set_angle(self.pointer_default)
        else:
            curr_pos = int(self._pointer_angle)
            max_pos = self.pointer_max_angle
            def_pos = self.pointer_default
            diff = def_pos - curr_pos
            if diff:
                step = 4 * int(diff / abs(diff))
                for i in range(curr_pos, def_pos, step):
                    self.set_angle(i)
                    self.Update()  # in this case, the buffer won't empty until update() is called
                    if i != 0:
                        time.sleep(ptw.easeInQuart(abs((curr_pos - i + 1) / diff)) / int(max_pos - def_pos * 0.75))
                        # TODO don't like sleeping the tween - threading version, maybe use position not time
        # Also extend function for clicking on a point animation
                self.set_angle(def_pos)
                self._pointer_limit_hit = None

    def _parse_limits(self, angle, max_angle):
        parsed_angle = angle
        if angle > self.pointer_max_angle:
            if self._pointer_limit_hit:
                parsed_angle = self._pointer_limit_hit
            else:
                if angle - max_angle < 360 - angle:
                    parsed_angle = self.pointer_max_angle
                else:
                    parsed_angle = self._pointer_min_angle
                self._pointer_limit_hit = parsed_angle
        else:
            self._pointer_limit_hit = None
        return parsed_angle

    @staticmethod
    def _parse_angle(angle, limit=360):
        return angle % limit

    @staticmethod
    def rotate_bmp(bmp, deg):
        radian = radians(deg)
        img = bmp.ConvertToImage()
        img_centre = rect_centre(img.GetSize())
        rot_img = img.Rotate(radian, (0, 0))
        rot_img_centre = rect_centre(rot_img.GetSize())
        offset = wx.Point(rot_img_centre - img_centre)
        rot_sub_img = rot_img.GetSubImage((wx.Rect(offset, img.GetSize())))
        rot_sub_bmp = rot_sub_img.ConvertToBitmap()
        return rot_sub_bmp


def angle_diff(point, origin):
    """ Returns the +ve clockwise angle from the origin to a point, (0 degrees is 3 o'clock) """
    dx = point[0] - origin[0]
    dy = point[1] - origin[1]
    rads = atan2(-dy, dx)
    rads %= 2 * pi
    degrees_ = 360 - degrees(rads)
    return degrees_


def rect_centre(size, origin=(0, 0)):
    """
    Returns the centre point of a rectangle

    :param size: wx.Size (width, height)
    :param origin: wx.Point (x,y) Top left co-ordinate
    :return: wx.Point: (x,y)
    """
    origin_x, origin_y = origin
    size_x, size_y = size
    centre_x = (size_x - origin_x) // 2
    centre_y = (size_y - origin_y) // 2
    return wx.Point(centre_x, centre_y)
