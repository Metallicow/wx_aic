import time

import wx
from wx.lib.newevent import NewCommandEvent
import pytweening as ptw

from aic import ActiveImageControl
from aic.util import make_padding

sss_cmd_event, EVT_SSS_CHANGE = NewCommandEvent()


class SimpleSlideSwitch(ActiveImageControl):

    def __init__(self, parent, bitmaps, is_vertical=False, max_pos=None, switch_ticks=2,
                 *args, **kwargs):
        """
        An Image Control for presenting a simple multi-position slide switch
        It behaves similarly to native radio buttons, in that only one value is selected at any one time (obj)

        :param bitmaps:  wx.BitMap objects - iterable (bmp,bmp)
                        (first bitmap will be the static background)
                        (the second will be the handle (pointer), preferably smaller than the static bitmap
                        If the handle is larger, you may need to compensate by adding padding to the slider
        :param is_vertical: Boolean - does the slider operate in a vertical orientation
        :param max_pos: Int - maximum limit of handle movement, pixel position relative to the zero position
                                in other words, the usable axis length (in pixels)
        :param switch_ticks:    an integer (>=2) which will spread the ticks evenly across the range
                                    or
                                an iterable of floats (0.0 - 1.0) as a % of axis max position (eg 0.5 is half way)
                                (the default is a 2 position switch with values of 0 & max)

        EVT_SSS_CHANGE: returns .value: int -> the (zero based) index of the selected switch position
        """

        super().__init__(parent, *args, **kwargs)
        # No borders + Wants Chars - to grab (cursor) key input
        self.SetWindowStyleFlag(wx.NO_BORDER | wx.WANTS_CHARS)

        self.parent = parent
        self.vertical = is_vertical
        self.static_bmp = bitmaps[0]
        self._static_size = self.static_bmp.Size
        self._static_padding = make_padding()
        self._static_pos = self._get_static_point()

        self.handle_bmp = bitmaps[1]
        self._handle_size = self.handle_bmp.Size
        self._handle_centre = rect_centre(self._handle_size)
        self._handle_offset = (0, 0)
        self._handle_max_pos = self._set_max(max_pos)
        self._handle_default = 0
        self._handle_pos = self._handle_default

        self._switch_ticks = switch_ticks  # either int or list of ints
        self._ticklist = self.make_ticklist(self._switch_ticks)  # list of tick values (int)
        self._tick_default = 0
        self._curr_tick = 0

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
        dc.DrawBitmap(self.static_bmp, self._static_pos)  # Draws foundation image
        dc.DrawBitmap(self.handle_bmp, self.get_handle_point())  # Draws handle image

        if self.highlight and self.HasFocus():
            self.draw_highlight(dc, self.GetSize(), self.highlight_box)

    def on_keypress(self, event):
        if self.HasFocus():
            keycode = event.GetKeyCode()

            if keycode in [wx.WXK_RIGHT, wx.WXK_UP]:
                if self.vertical:
                    self.set_tick(self._curr_tick - self._cursor_key_step)
                else:
                    self.set_tick(self._curr_tick + self._cursor_key_step)
            elif keycode in [wx.WXK_LEFT, wx.WXK_DOWN]:
                if self.vertical:
                    self.set_tick(self._curr_tick + self._cursor_key_step)
                else:
                    self.set_tick(self._curr_tick - self._cursor_key_step)

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
        delta = event.GetWheelDelta()  # usually +/-120, but it's better not to assume
        if self.vertical:
            self.set_tick(self._curr_tick - self._scroll_wheel_step * event.GetWheelRotation() // delta)
        else:
            self.set_tick(self._curr_tick + self._scroll_wheel_step * event.GetWheelRotation() // delta)

    def on_left_down(self, event):
        self.mouse_move(event.GetPosition())

    def on_left_drag(self, event):
        if event.Dragging() and event.LeftIsDown():
            self.mouse_move(event.GetPosition())
        event.Skip()

    def mouse_move(self, mouse_pos):
        # find nearest tick then set current tick to it
        if not self.HasFocus():
            self.SetFocus()
            if self._evt_on_focus:
                self._send_event()
        index = self.vertical
        position = mouse_pos[index] - self._handle_centre[index] - self._static_padding[3 - (3 * index)]
        closest_tick = min(range(len(self._ticklist)), key=lambda i: abs(self._ticklist[i] - position))
        self.set_tick(closest_tick)

    def on_middle_up(self, _):
        if not self.HasFocus():
            self.SetFocus()
            if self._evt_on_focus:
                self._send_event()
        self.reset_position()

    def make_ticklist(self, ticks):
        tick_list = []
        max_ = self._handle_max_pos
        if isinstance(ticks, int):  # if a single number is passed
            # print(f'max= {self._handle_max_pos}')
            if 1 < ticks <= max_:
                for t in range(0, ticks):
                    tick = int(t * max_ / (ticks - 1))
                    tick_list.append(tick)
            else:
                raise ValueError(f'switch_ticks: Expected a value from 2 - {max_}')
        else:
            if len(ticks) > 1:  # otherwise assume that an iterable of integers is passed
                # print(f'found {len(ticks)} ticks')
                # print(ticks)
                for tick in ticks:
                    tick_list.append(int(tick * max_))  # horizontal
            else:
                raise IndexError(f'switch_ticks: Expected 2 or more ticks')
        return tick_list

    # Getters and Setters #
    def _set_max(self, pos):
        """ Set the maximum pixel position value for the handle """
        index = self.vertical
        if pos:
            if 0 <= pos <= self._static_size[index]:
                return pos
        return self._static_size[index]

    def _get_static_point(self):
        """ Returns the point at the top left of the foundation image """
        winx, winy = self.GetPosition()
        pady, _, _, padx = self._static_padding
        point = (winx + padx, winy + pady)
        return point

    def set_padding(self, pad=(0, 0, 0, 0)):
        """ Apply additional padding around the static image, mouse events will extend into the padding """
        self._static_padding = make_padding(pad)
        self._static_pos = self._get_static_point()

    def get_handle_point(self):
        x_base = self._static_pos[0] + self._handle_offset[0]
        y_base = self._static_pos[1] + self._handle_offset[1]

        if self.vertical:
            return x_base, self._handle_pos + y_base
        else:
            return self._handle_pos + x_base, y_base

    def set_default_tick(self, tick=0):
        """ Set the default tick position for the handle, resetting will place the handle at this point"""
        if 0 <= tick < len(self._ticklist):  # make sure the tick value is within range
            self.set_tick(tick)
            self._tick_default = tick
            self._handle_default = self._handle_pos  # TODO not sure if this is needed any more
        else:
            raise ValueError('The tick value is not within range')

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

    def set_tick(self, tick):
        """ Validate and Set the tick value and the position for the handle """
        if tick < 0:  # make sure the tick value is within range - adjust if not
            tick = 0
        elif tick >= len(self._ticklist):
            tick = len(self._ticklist) - 1
        if tick != self._curr_tick:
            self._curr_tick = tick
            self.set_position(self._ticklist[tick])
            self.Refresh(True)

    def set_position(self, pos=0):
        """ Parse and Set the (actual pixel) position for the handle """
        valid_pos = self._validate_limits(pos, self._handle_max_pos)
        if valid_pos != self._handle_pos:
            self._handle_pos = valid_pos
            self._send_event()
            self.Refresh(True)

    def reset_position(self, animate=True):

        self._animate(self._tick_default, animate)

    # Properties #
    @property
    def value(self):
        return self._curr_tick  # index

    @value.setter
    def value(self, tick):
        self.set_tick(tick)

    # Animation methods #
    def _animate(self, destination, animate=True):
        if animate:
            max_pos = self._handle_max_pos
            curr_pos = self._ticklist[self._curr_tick]
            dest_pos = self._ticklist[destination]
            diff = dest_pos - curr_pos
            if diff:
                step_dir = int(diff / abs(diff))
                step = 4 * step_dir
                for i in range(curr_pos, dest_pos, step):
                    self.set_position(i)
                    # because we are using sleep in a loop, we are not returning control to the main loop
                    # so we need to call update() to refresh the screen immediately - ie to 'animate'
                    self.Update()
                    if i != 0:
                        time.sleep(ptw.easeInQuart(abs((curr_pos - i + 1) / diff)) / int(max_pos * 0.85))

        self.set_tick(self._tick_default)

    # Helper methods #
    @staticmethod
    def _validate_limits(position, max_pos):
        """ Validate a position value, correcting the value if it exceeds lower or upper parameters """
        if position > max_pos:
            return max_pos
        elif position < 0:
            return 0
        return position

    @staticmethod
    def _within_boundary(point, boundary):
        """ checks that a point is within the boundary of the foundation image """
        if (0 <= point[0] <= boundary[0]) and (0 <= point[1] <= boundary[1]):
            return True
        else:
            raise ValueError('The position value is not within the boundary of the slider widget')

    def _send_event(self):
        wx.PostEvent(self, sss_cmd_event(id=self.GetId(), value=self.value))


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
