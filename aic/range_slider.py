import time

import wx
from wx.lib.newevent import NewCommandEvent
import pytweening as ptw
from aic import ActiveImageControl
from aic.utilities import make_padding

rs_cmd_event, EVT_RS_CHANGE = NewCommandEvent()


class RangeSlider(ActiveImageControl):

    def __init__(self, parent, bitmaps, is_vertical=False, is_inverted=False, max_pos=None, *args, **kwargs):
        """
        An Image Control for presenting a simple slider style
        It behaves similarly to a native control slider, except value is expressed as a percentage

        :param bitmaps:  wx.BitMap objects - iterable (bmp,bmp,[bmp])
                        (first bitmap will be the static background)
                        (the second will be the handle/s (pointers), preferably smaller than the static bitmap)
                        (if a third bitmap is passed, it will apply to the 'high' handle only)
                        If the handle is larger, you may need to compensate by adding padding to the slider
        :param is_vertical: Boolean - does the slider operate in a vertical orientation
        :param is_inverted: Boolean - does the slider operate contra to the co-ordinate system
                            Put simply:
                                on a horizontal slider- True if the right-most position has a zero value
                                on a vertical slider- True if the bottom-most position has a zero value
        :param max_pos: Int - maximum limit of handle movement, pixel position relative to the zero position

        EVT_RS_CHANGE: returns .value: (float(0-1), float(0-1)) ->  the position of the (low, high) handles as a
                                                                    percentage of the slider range
        """

        super().__init__(parent, *args, **kwargs)
        # Wants Chars used so that we can grab (cursor) key input
        # self.SetWindowStyleFlag(wx.WANTS_CHARS)
        self.SetWindowStyleFlag(wx.NO_BORDER | wx.WANTS_CHARS)

        self.parent = parent
        self.vertical = is_vertical
        self.inverted = is_inverted  # False for lt->rt & top->bot layouts; True for rt->lt & bot->top layouts
        self.stat_bmp = bitmaps[0]
        self._static_size = self.stat_bmp.Size
        self._static_padding = make_padding()
        self._static_pos = self._get_stat_point()

        self.handle_lo_bmp = bitmaps[1]
        self._handle_lo_size = self.handle_lo_bmp.Size
        self._handle_lo_centre = rect_centre(self._handle_lo_size)
        self._handle_lo_default = 0
        self._handle_lo_pos = self._handle_lo_default

        self.handle_hi_bmp = bitmaps[1] if len(bitmaps) == 2 else bitmaps[2]
        self._handle_hi_size = self.handle_hi_bmp.Size
        self._handle_hi_centre = rect_centre(self._handle_hi_size)
        self._handle_hi_default = 0
        self._handle_hi_pos = self._handle_hi_default

        self._handle_max_pos = self._set_max(max_pos)
        self._handle_offset = (0, 0)

        self._scroll_wheel_step = 1
        self._cursor_key_step = 1
        self._evt_on_focus = False
        # self._evt_on_animate = True   # enable when threaded animation is used

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
        w, h = self._static_size
        pad_y1, pad_x2, pad_y2, pad_x1 = self._static_padding
        size = wx.Size(w + pad_x1 + pad_x2, h + pad_y1 + pad_y2)
        return size

    # Event handling #
    def on_paint(self, _):
        window_rect = self.GetRect()
        buffer_bitmap = self.parent.bg_render.GetSubBitmap(window_rect)
        self.draw_to_context(wx.BufferedPaintDC(self, buffer_bitmap))

    def draw_to_context(self, dc):
        dc.DrawBitmap(self.stat_bmp, self._static_pos)  # Draws foundation image
        dc.DrawBitmap(self.handle_hi_bmp, self.get_handle_point(self._handle_hi_pos))  # Draws handle high image
        dc.DrawBitmap(self.handle_lo_bmp, self.get_handle_point(self._handle_lo_pos))  # Draws handle low image

        if self.highlight and self.HasFocus():
            self.draw_highlight(dc, self.GetSize(), self.highlight_box)

    def on_keypress(self, event):
        if self.HasFocus():
            keycode = event.GetKeyCode()

            if keycode in [wx.WXK_RIGHT, wx.WXK_UP]:
                if (self.inverted and not self.vertical) or (self.vertical and not self.inverted):
                    self.set_position_low(self._handle_lo_pos - self._cursor_key_step)
                else:
                    self.set_position_low(self._handle_lo_pos + self._cursor_key_step)

            elif keycode in [wx.WXK_LEFT, wx.WXK_DOWN]:
                if (self.inverted and not self.vertical) or (self.vertical and not self.inverted):
                    self.set_position_low(self._handle_lo_pos + self._cursor_key_step)
                else:
                    self.set_position_low(self._handle_lo_pos - self._cursor_key_step)

            elif keycode == wx.WXK_SPACE:
                self.reset_position()

            elif keycode == wx.WXK_TAB:
                self.Navigate(not (event.ShiftDown()))  # Navigates backwards if 'shift' key is held

        event.Skip()

    def on_mouse_wheel(self, event):
        if not self.HasFocus():
            self.SetFocus()
            if self._evt_on_focus:
                self._send_event()
        delta = event.GetWheelDelta()  # normally +/-120, but better not to assume
        if (self.inverted and not self.vertical) or (self.vertical and not self.inverted):
            self.set_position_low(self._handle_lo_pos - (self._scroll_wheel_step * event.GetWheelRotation() // delta))
        else:
            self.set_position_low(self._handle_lo_pos + (self._scroll_wheel_step * event.GetWheelRotation() // delta))

    def on_left_down(self, event):
        self.mouse_move(event.GetPosition(), True)

    def on_left_drag(self, event):
        if event.Dragging() and event.LeftIsDown():
            self.mouse_move(event.GetPosition())
        event.Skip()

    def mouse_move(self, mouse_pos, animate=False):
        if not self.HasFocus():
            self.SetFocus()
            if self._evt_on_focus:
                self._send_event()
        index = self.vertical
        position = mouse_pos[index] - self._handle_lo_centre[index] - self._static_padding[3 - (3 * index)]
        if self.inverted:
            position = self._handle_max_pos - position
        self._animate(position, animate)
        # self.set_position_low(position)

    def on_middle_up(self, _):
        if not self.HasFocus():
            self.SetFocus()
            if self._evt_on_focus:
                self._send_event()
        self.reset_position()

    # Getters and Setters #
    def set_padding(self, pad=(0, 0, 0, 0)):
        """ Apply additional padding around the static image, mouse events will extend into the padding """
        self._static_padding = make_padding(pad)
        self._static_pos = self._get_stat_point()

    def _get_stat_point(self):
        """ Returns the point at the top left of the foundation image """
        winx, winy = self.GetPosition()
        pady, _, _, padx = self._static_padding
        point = (winx + padx, winy + pady)
        return point

    def get_handle_point(self, handle_pos):
        x_base = self._static_pos[0] + self._handle_offset[0]
        y_base = self._static_pos[1] + self._handle_offset[1]
        if self.inverted:
            if self.vertical:
                return x_base, self._handle_max_pos - handle_pos + y_base
            else:
                return self._handle_max_pos - handle_pos + x_base, y_base
        else:
            if self.vertical:
                return x_base, handle_pos + y_base
            else:
                return handle_pos + x_base, y_base

    def set_default_pos(self, pos=0):
        """ Set the default pixel position for the handle, a reset will place the handle at this point"""        
        valid_pos = self._validate_limit(pos, self._handle_max_pos)
        self._handle_lo_default = valid_pos
        self.set_position_low(self._handle_lo_default)

    def set_default_values(self, values=(0, 1)):
        """ Set the default position for the handles - as percentage values; correcting if values are swapped """
        v_low, v_high = values
        if v_low > v_high:
            v_high, v_low = values
        self.set_default_value_low(v_low)
        self.set_default_value_high(v_high)

    def set_default_value_low(self, val=0):
        """ Set the default position for the handle - as a percentage value """
        valid_value = self._validate_limit(val, 1)
        self._handle_lo_default = int(valid_value * self._handle_max_pos)
        self.set_position_low(self._handle_lo_default)

    def set_default_value_high(self, val=1):
        """ Set the default position for the handle - as a percentage value """
        valid_value = self._validate_limit(val, 1)
        self._handle_hi_default = int(valid_value * self._handle_max_pos)
        self.set_position_low(self._handle_hi_default)

    def _set_max(self, pos):
        """ Set the maximum position value for the high handle """
        index = self.vertical
        if pos:
            if 0 <= pos <= self._static_size[index]:
                return pos - self._handle_hi_size[index]    # position adjusted so that the high handle fits in
        return self._static_size[index] - self._handle_hi_size[index]

    def set_offset(self, point=(0, 0)):
        """ Set the offset for the handle: x,y co-ordinates relative to the top left corner of the foundation image """
        if self._within_boundary(point, self._static_size):
            self._handle_offset = point

    def set_step(self, scroll=1, key=1):
        """ Set the increment value for the scroll-wheel and cursor keys (int > 0) """
        self.set_scroll_step(scroll)
        self.set_key_step(key)

    def set_scroll_step(self, step=1):
        """ Set the scroll-wheel step size (int > 0) """
        self._scroll_wheel_step = step

    def set_key_step(self, step=1):
        """ Set cursor key step size (int > 0) """
        self._cursor_key_step = step

    def set_position_low(self, pos=0):
        """ Validate and Set the (actual pixel) position for the handle """
        valid_pos = self._validate_limit(pos, self._handle_max_pos)
        if valid_pos != self._handle_lo_pos:
            self._handle_lo_pos = valid_pos
            self._send_event()
            self.Refresh(True)

    def set_evt_on_focus(self, val=True):
        self._evt_on_focus = val

    # def set_evt_on_animate(self, val = True): # enable when threaded animation is used
    #     self._evt_on_animate = val

    def reset_position(self, animate=True):
        self._animate(self._handle_lo_default, animate)

    # Properties #
    @property
    def value(self):
        value_lo = self._handle_lo_pos / self._handle_max_pos   # TODO - one or both of these values must compensate for
        value_hi = self._handle_hi_pos / self._handle_max_pos   # width of the handle/s, ?
        return value_lo, value_hi  # as percentage of the max value

    @value.setter
    def value(self, percent):
        self.set_position_low(percent * self._handle_max_pos)

    # TODO work on alternative animation method, threading? Can't use wx.timer as it's too slow
    # Also consider variables for speed factor(0.85) and smoothness(step=4)

    # Animation methods #
    def _animate(self, destination, animate=True):
        if animate:
            curr_pos = self._handle_lo_pos
            max_pos = self._handle_max_pos
            def_pos = destination
            diff = def_pos - curr_pos
            if diff:
                step = 4 * int(diff / abs(diff))
                for i in range(curr_pos, def_pos, step):
                    self.set_position_low(i)
                    # if self._evt_on_animate:  # This may be reserved for threaded animation
                    #     self._send_event()
                    #     print('sent')
                    # because we are using sleep in a loop, we are not returning control to the main loop
                    # so we need to call update() to refresh the screen immediately - ie to 'animate'
                    self.Update()
                    if i != 0:
                        time.sleep(ptw.easeInQuart(abs((curr_pos - i + 1) / diff)) / int(max_pos * 0.85))

        self.set_position_low(destination)

    # Helper methods #
    def _validate_limit(self, position, max_pos):
        """ Validate a position value, correcting the value if it exceeds lower or upper parameters """
        if position > max_pos:
            return max_pos
        elif position < 0:
            return 0
        return position

    def _within_boundary(self, point, boundary):
        """ checks that a point is within the boundary of the foundation image """
        if (0 <= point[0] <= boundary[0]) and (0 <= point[1] <= boundary[1]):
            return True
        else:
            raise ValueError('The position value is not within the boundary of the slider widget')

    def _send_event(self):
        wx.PostEvent(self, rs_cmd_event(id=self.GetId(), value=self.value))


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
