import time

import wx
from wx.lib.newevent import NewCommandEvent
import pytweening as ptw
from aic import ActiveImageControl
from aic.util import make_padding

rs_cmd_event, EVT_RS_CHANGE = NewCommandEvent()


class RangeSlider(ActiveImageControl):

    def __init__(self, parent, bitmaps, is_vertical=False, is_inverted=False, max_pos=None, *args, **kwargs):
        """
        An Image Control for presenting a range slider style
        It behaves as a double point native control slider; handle values are expressed as percentages

        :param bitmaps:  wx.BitMap objects - iterable (bmp,bmp,[bmp])
                        (first bitmap will be the static background)
                        (the second will be the handle/s (pointers), preferably smaller than the static bitmap)
                        (if a third bitmap is passed, it will apply to the 'high' handle only)
                        If the handle is large, you may need to compensate by adding padding to the slider
        :param is_vertical: Boolean - does the slider operate in a vertical orientation
        :param is_inverted: Boolean - does the slider operate contra to the co-ordinate system
                            Put simply:
                                on a horizontal slider- True if the right-most position has a zero value
                                on a vertical slider- True if the bottom-most position has a zero value
        :param max_pos: Int - maximum limit of handle movement, pixel position relative to the zero position
                                in other words, the usable axis length (in pixels)

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

        self.handle_bmp = self._set_handle_bitmaps(bitmaps)
        self._handle_size = self.handle_bmp[0].Size, self.handle_bmp[1].Size
        self._handle_centre = rect_centre(self._handle_size[0]), rect_centre(self._handle_size[1])
        self._handle_default = [0, 0]
        self._handle_pos = [self._handle_default[0], self._handle_default[1]]

        self._handle_max_pos = self._set_max(max_pos)
        self._handle_offset = (0, 0)

        self._scroll_wheel_step = 1
        self._cursor_key_step = 1

        self.range_bar = 1  # 0 = disabled; 1 enabled - passive; 2 enabled - active
        self.bar_colour = wx.Colour(250, 250, 25, 205)
        self.bar_shrink = 7

        self.animated = True
        self._active_handle = 0  # 0 for lo handle; 1 for hi handle
        self._not_dragging = True
        self._last_mouse_pos = None
        self._evt_on_focus = False
        # self._evt_on_animate = True   # enable when threaded animation is used;
        # Used to generate an event for each step of the animation (currently sends event at completion of animation)

        self.highlight_box = ((0, 0), (0, 0))

        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.Bind(wx.EVT_PAINT, self.on_paint)

        self.Bind(wx.EVT_KEY_DOWN, self.on_keypress)
        self.Bind(wx.EVT_LEFT_DOWN, self.on_left_down)
        self.Bind(wx.EVT_LEFT_UP, self.on_mouse_button_up)
        self.Bind(wx.EVT_MIDDLE_DOWN, self.on_middle_down)
        self.Bind(wx.EVT_MIDDLE_UP, self.on_middle_up)
        self.Bind(wx.EVT_RIGHT_UP, self.on_mouse_button_up)
        self.Bind(wx.EVT_MOUSEWHEEL, self.on_mouse_wheel)
        self.Bind(wx.EVT_MOUSE_EVENTS, self.on_mouse_drag)
        self.Bind(wx.EVT_LEAVE_WINDOW, self.on_leave)

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
        hi_point = self.get_handle_point(self._handle_pos[1], True)
        lo_point = self.get_handle_point(self._handle_pos[0])
        if self.range_bar:
            self.draw_bar(dc, lo_point, hi_point)
        dc.DrawBitmap(self.handle_bmp[1], hi_point)  # Draws handle high image
        dc.DrawBitmap(self.handle_bmp[0], lo_point)  # Draws handle low image

        if self.highlight and self.HasFocus():
            self.draw_highlight(dc, self.GetSize(), self.highlight_box)

    def draw_bar(self, context, lo_point, hi_point):
        try:
            dc = wx.GCDC(context)
        except NotImplementedError:
            dc = context
        if self.vertical:
            offset = (-1, 0)
        else:
            offset = (0, -1)
        if self.inverted:
            lo_x, lo_y = hi_point
            hi_x, hi_y = lo_point
        else:
            lo_x, lo_y = lo_point
            hi_x, hi_y = hi_point

        rect_point = lo_x + offset[0], lo_y + offset[1]
        if self.vertical:
            rect_size = self._handle_size[0][0], hi_y - lo_y + self._handle_size[0][1]
        else:
            rect_size = hi_x - lo_x + self._handle_size[0][0], self._handle_size[0][1]
        pen_col = brush_col = self.bar_colour
        dc.SetPen(wx.Pen(pen_col, width=1))
        dc.SetBrush(wx.Brush(brush_col))
        rect = wx.Rect(rect_point, rect_size)
        dc.DrawRectangle(rect.Deflate(self.bar_shrink))

        colour = wx.Colour(250, 25, 25, 60)
        if self.vertical:
            rect_point = lo_x + offset[0] + 1, lo_y + offset[1]
            rect_size = self._handle_size[0][0] - 1, hi_y - lo_y + self._handle_size[0][1]
        else:
            rect_point = lo_x + offset[0], lo_y + offset[1] + 1
            rect_size = hi_x - lo_x + self._handle_size[0][0], self._handle_size[0][1] - 1
        pen_col = brush_col = colour
        dc.SetPen(wx.Pen(pen_col, width=1))
        dc.SetBrush(wx.Brush(brush_col))
        rect = wx.Rect(rect_point, rect_size)
        dc.DrawRectangle(rect.Deflate(self.bar_shrink))

        colour = wx.Colour(55, 25, 25, 35)
        if self.vertical:
            rect_point = lo_x + offset[0] + 4, lo_y + offset[1]
            rect_size = self._handle_size[0][0] - 4, hi_y - lo_y + self._handle_size[0][1]
        else:
            rect_point = lo_x + offset[0], lo_y + offset[1] + 4
            rect_size = hi_x - lo_x + self._handle_size[0][0], self._handle_size[0][1] - 4
        pen_col = brush_col = colour
        dc.SetPen(wx.Pen(pen_col, width=1))
        dc.SetBrush(wx.Brush(brush_col))
        rect = wx.Rect(rect_point, rect_size)
        dc.DrawRectangle(rect.Deflate(self.bar_shrink))

    def on_keypress(self, event):
        if self.HasFocus():
            keycode = event.GetKeyCode()

            if keycode in [wx.WXK_RIGHT, wx.WXK_UP]:
                if (self.inverted and not self.vertical) or (self.vertical and not self.inverted):
                    self.set_position(self._handle_pos[self._active_handle] - self._cursor_key_step)
                else:
                    self.set_position(self._handle_pos[self._active_handle] + self._cursor_key_step)

            elif keycode in [wx.WXK_LEFT, wx.WXK_DOWN]:
                if (self.inverted and not self.vertical) or (self.vertical and not self.inverted):
                    self.set_position(self._handle_pos[self._active_handle] + self._cursor_key_step)
                else:
                    self.set_position(self._handle_pos[self._active_handle] - self._cursor_key_step)

            elif keycode == wx.WXK_SPACE:
                self.reset_position()

            elif keycode == wx.WXK_CONTROL:  # Ctrl key toggle the active handle (for keyboard nav)
                self._active_handle = not self._active_handle

            elif keycode == wx.WXK_TAB:
                self.Navigate(not (event.ShiftDown()))  # Navigates backwards if 'shift' key is held

        event.Skip()

    def on_mouse_wheel(self, event):
        if not self.HasFocus():
            self.SetFocus()
            if self._evt_on_focus:
                self._send_event()

        mouse_pos = event.GetPosition()
        index = self.vertical
        rel_mouse_pos = mouse_pos[index] - self._handle_offset[index] - \
                        self._static_padding[3 - (3 * index)] - self._handle_size[0][index]
        self._active_handle = self._closest_handle(rel_mouse_pos)

        delta = event.GetWheelDelta()  # normally +/-120, but better not to assume
        if (self.inverted and not self.vertical) or (self.vertical and not self.inverted):
            self.set_position(
                self._handle_pos[self._active_handle] - (self._scroll_wheel_step * event.GetWheelRotation() // delta))
        else:
            self.set_position(
                self._handle_pos[self._active_handle] + (self._scroll_wheel_step * event.GetWheelRotation() // delta))

    def on_left_down(self, event):
        self.mouse_move(event.GetPosition(), self.animated)

    def on_mouse_drag(self, event):
        if event.Dragging() and event.LeftIsDown():
            self.mouse_move(event.GetPosition())
        if event.Dragging() and event.RightIsDown():
            if self.range_bar == 2:
                self.bar_move(event.GetPosition())
        event.Skip()

    def on_mouse_button_up(self, _):
        self._not_dragging = True
        self._last_mouse_pos = None

    def bar_move(self, mouse_pos):
        if not self.HasFocus():
            self.SetFocus()
            if self._evt_on_focus:
                self._send_event()

        diff = abs(self._handle_pos[1] - self._handle_pos[0])
        if diff != self._handle_max_pos:  # if range bar is at maximum width, do nothing (since it can't move)
            index = self.vertical
            if self.inverted:
                rel_mouse_pos = self._rel_mouse_position(mouse_pos, index) + diff//2
            else:
                rel_mouse_pos = self._rel_mouse_position(mouse_pos, index) - diff//2

            if self._last_mouse_pos is None:  # if we have only started to move the mouse, just save it's position
                self._last_mouse_pos = rel_mouse_pos
            else:
                move = rel_mouse_pos - self._last_mouse_pos

                if move:
                    # if movement is -ve, test the lo handle, if +ve, test the hi handle
                    if move == abs(move):
                        if self.inverted:
                            print(self._handle_pos[1],move, diff, self._handle_max_pos)
                            new_pos = self._validate_limit(self._handle_pos[1] + move, self._handle_max_pos) - diff #TODO
                            print(new_pos)
                        else:
                            print(self._handle_pos[1],move, diff, self._handle_max_pos)
                            new_pos = self._validate_limit(self._handle_pos[1] + move, self._handle_max_pos) - diff
                            print(new_pos)

                    else:
                        if self.inverted:
                            new_pos = self._validate_limit(self._handle_pos[0] + move, self._handle_max_pos) #TODO
                        else:
                            new_pos = self._validate_limit(self._handle_pos[0] + move, self._handle_max_pos)

                    if new_pos != self._handle_pos[self.inverted]:
                        # print(self._handle_pos[0], new_pos)
                        if self.inverted:
                            new_pos = self._handle_max_pos - new_pos
                            self._active_handle = 0
                            self.set_position(new_pos-diff)
                            self._active_handle = 1
                            self.set_position(new_pos)
                        else:
                            self._active_handle = 0
                            self.set_position(new_pos)
                            self._active_handle = 1
                            self.set_position(new_pos+diff)
                        self._last_mouse_pos =  new_pos

            # self._notdragging = False  # TODO may not be needed

    def mouse_move(self, mouse_pos, animate=False):
        if not self.HasFocus():
            self.SetFocus()
            if self._evt_on_focus:
                self._send_event()
        index = self.vertical
        hand_max = self._handle_max_pos
        rel_mouse_pos = self._rel_mouse_position(mouse_pos, index)

        if self._not_dragging:
            self._active_handle = self._closest_handle(rel_mouse_pos)
            self._not_dragging = False

        if self._active_handle:
            rel_mouse_pos = mouse_pos[index] \
                            - (3 * self._handle_centre[1][index]) \
                            - self._static_padding[3 - (3 * index)]
        else:
            rel_mouse_pos = mouse_pos[index] \
                            - self._handle_centre[0][index] \
                            - self._static_padding[3 - (3 * index)]
        if self.inverted:
            if self._active_handle:
                rel_mouse_pos = hand_max - rel_mouse_pos - (self._handle_size[1][index])
            else:
                rel_mouse_pos = hand_max - rel_mouse_pos + (self._handle_size[1][index])
        self._move_handle(rel_mouse_pos, animate)

    def _rel_mouse_position(self, mouse_pos, index):
        """ Return an integer representing the mouse position relative to the slider axis """
        return mouse_pos[index] \
               - self._handle_offset[index] \
               - self._static_padding[3 - (3 * index)] \
               - self._handle_size[0][index]

    def _closest_handle(self, mouse_pos):
        hand_pos = self._handle_pos
        if self.inverted:
            mouse_pos = self._handle_max_pos - mouse_pos
        if mouse_pos <= hand_pos[0]:
            return 0
        elif mouse_pos >= hand_pos[1]:
            return 1
        else:
            if self.inverted:
                return min(range(2), key=lambda i: abs(mouse_pos - hand_pos[i]))
            else:
                return min(range(2), key=lambda i: abs(hand_pos[i] - mouse_pos))

    def on_leave(self, _):
        self._not_dragging = True
        self._last_mouse_pos = None

    def on_middle_down(self, event):
        if not self.HasFocus():
            self.SetFocus()
            if self._evt_on_focus:
                self._send_event()
        mouse_pos = event.GetPosition()
        index = self.vertical
        rel_mouse_pos = mouse_pos[index] - self._handle_offset[index] - \
                        self._static_padding[3 - (3 * index)] - self._handle_size[0][index]
        self._active_handle = self._closest_handle(rel_mouse_pos)

    def on_middle_up(self, _):
        self.reset_position()

    # Getters and Setters #
    def set_padding(self, pad=(0, 0, 0, 0)):
        """ Apply additional padding around the static image, mouse events will extend into the padding """
        self._static_padding = make_padding(pad)
        self._static_pos = self._get_stat_point()

    def set_active_handle(self, handle):
        self._active_handle = handle

    def _get_stat_point(self):
        """ Returns the point at the top left of the foundation image """
        winx, winy = self.GetPosition()
        pady, _, _, padx = self._static_padding
        point = (winx + padx, winy + pady)
        return point

    def get_handle_point(self, handle_pos, is_hi_handle=False):
        """ Returns the top-left point for drawing a handle (either hi or lo) """
        x_base = self._static_pos[0] + self._handle_offset[0]
        y_base = self._static_pos[1] + self._handle_offset[1]
        inv_base = self._handle_max_pos - handle_pos
        if self.inverted:
            if self.vertical:
                if is_hi_handle:
                    return x_base, inv_base + y_base
                else:
                    return x_base, inv_base + self._handle_size[0][1] + y_base
            else:
                if is_hi_handle:
                    return inv_base + x_base, y_base
                else:
                    return inv_base + x_base + self._handle_size[0][0], y_base

        else:
            if self.vertical:
                if is_hi_handle:
                    return x_base, handle_pos + self._handle_size[0][1] + y_base
                return x_base, handle_pos + y_base
            else:
                if is_hi_handle:
                    return handle_pos + x_base + self._handle_size[0][0], y_base
                return handle_pos + x_base, y_base

    def set_default_pos(self, pos=0):  # TODO
        """ Set the default pixel position for the handle, a reset will place the handle at this point"""
        valid_pos = self._validate_limit(pos, self._handle_max_pos)
        self._handle_default = valid_pos
        self.set_position(self._handle_default)

    def set_default_values(self, values=(0, 1)):
        """ Set the default position for the handles - as percentage values; correcting if values are swapped """
        v_low, v_high = values
        if v_low > v_high:
            v_high, v_low = values
        self.set_default_value_low(v_low)
        self.set_default_value_high(v_high)
        self._active_handle = 0

    def set_default_value_low(self, val=0):
        """ Set the default position for the handle - as a percentage value """
        self._active_handle = 0
        valid_value = self._validate_limit(val, 1)
        self._handle_default[0] = int(valid_value * self._handle_max_pos)
        self.set_position(self._handle_default[0])

    def set_default_value_high(self, val=1):
        """ Set the default position for the handle - as a percentage value """
        self._active_handle = 1
        valid_value = self._validate_limit(val, 1)
        self._handle_default[1] = int(valid_value * self._handle_max_pos)
        self.set_position(self._handle_default[1])

    def _set_max(self, pos):
        """ Set the maximum position value for the low handle """
        index = self.vertical
        if pos:
            if 0 <= pos <= self._static_size[index]:
                return pos - self._handle_size[1][index]  # position adjusted to accommodate the 'high' handle
        return self._static_size[index] - self._handle_size[1][index]

    def _set_handle_bitmaps(self, bitmaps):
        if self.inverted:
            handles = bitmaps[1] if len(bitmaps) == 2 else bitmaps[2], bitmaps[1]
        else:
            handles = bitmaps[1], bitmaps[1] if len(bitmaps) == 2 else bitmaps[2]
        return handles

    def set_offset(self, point=(0, 0)):
        """ Set the offset for the handles: x,y co-ordinates relative to the top left corner of the foundation image """
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

    def set_position(self, pos=0):
        """ Validate and Set the (actual pixel) position for the handle """
        valid_pos = self._validate_limit(pos, self._handle_max_pos)
        if valid_pos != self._handle_pos[self._active_handle]:
            self._handle_pos[self._active_handle] = valid_pos
            if self._active_handle:
                if self._handle_pos[0] > self._handle_pos[1]:
                    self._handle_pos[0] = self._handle_pos[1]
            elif self._handle_pos[1] < self._handle_pos[0]:
                self._handle_pos[1] = self._handle_pos[0]
            self._send_event()
            self.Refresh(True)

    def set_evt_on_focus(self, val=True):
        self._evt_on_focus = val

    # def set_evt_on_animate(self, val = True): # enable when threaded animation is used
    #     self._evt_on_animate = val

    def reset_position(self):
        self._move_handle(self._handle_default[self._active_handle], self.animated)

    # Properties #
    @property
    def value(self):
        value_lo = self._handle_pos[0] / self._handle_max_pos  # TODO - one or both of these values must compensate for
        value_hi = self._handle_pos[1] / self._handle_max_pos  # width of the handle/s, ?
        return value_lo, value_hi  # as percentage of the max value

    @value.setter
    def value(self, percent):
        self.set_position(percent * self._handle_max_pos)

    # TODO work on alternative animation method, threading? Can't use wx.timer as it's too slow
    # Also consider variables for speed factor(0.85) and smoothness(step=4)

    # Animation methods #
    def _move_handle(self, destination, animate=True):
        if animate:
            curr_pos = self._handle_pos[self._active_handle]
            max_pos = self._handle_max_pos
            dest_pos = self._validate_limit(destination, max_pos)
            diff = dest_pos - curr_pos
            if diff:
                step = 4 * int(diff / abs(diff))
                for i in range(curr_pos, dest_pos, step):
                    self.set_position(i)
                    # if self._evt_on_animate:  # This may be reserved for threaded animation
                    #     self._send_event()
                    #     print('sent')
                    # because we are using sleep in a loop, we are not returning control to the main loop
                    # so we need to call update() to refresh the screen immediately - ie to 'animate'
                    self.Update()
                    if i != 0:
                        time.sleep(ptw.easeInQuart(abs((curr_pos - i + 1) / diff)) / int(max_pos * 0.85))

        self.set_position(destination)

    # Helper methods #
    @staticmethod
    def _validate_limit(position, max_pos):
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
