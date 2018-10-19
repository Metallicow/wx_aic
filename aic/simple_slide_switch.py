import time

import wx
from wx.lib.newevent import NewCommandEvent
import pytweening as ptw

from aic import ActiveImageControl

sss_cmd_event, EVT_SSS_CHANGE = NewCommandEvent()


class SimpleSlideSwitch(ActiveImageControl):

    def __init__(self, parent, bitmaps, is_vertical=False, is_inverted=False, switch_ticks=2,
                 *args, **kwargs):
        """
        An Image Control for presenting a rotary dial style, (eg a knob or dial type control)
        It behaves similarly to a native control slider, except value is expressed as degrees (float)

        :param bitmaps:  wx.BitMap objects - iterable
                        (first bitmap will be the static background)
                        (the second will be the handle (pointer), preferably smaller than the static bitmap
                        If the handle is larger, you may need to compensate by adding padding to the slider
        :param is_vertical: Boolean - does the slider operate in a vertical orientation
        :param is_inverted: Boolean - do the values need to be contra to the co-ordinate system
                            Put simply:
                                on a horizontal slider- True if the right-most position has a zero value
                                on a vertical slider- True if the bottom-most position has a zero value
        :param switch_ticks:    an integer (>=2) will spread the ticks evenly across the range (defaults: 0 & max)
                                    or
                                an iterable of floats (0.0 - 1.0) as a % of axis max position (eg 0.5 is half way)

        EVT_SSS_CHANGE: returns .value: int ->  the index of the selected switch position
        """

        super().__init__(parent, *args, **kwargs)
        # No borders + Wants Chars - to grab (cursor) key input
        self.SetWindowStyleFlag(wx.NO_BORDER | wx.WANTS_CHARS)

        self.parent = parent
        self.vertical = is_vertical
        self.inverted = is_inverted  # False for lt->rt & top->bot layouts; True for rt->lt & bot->top layouts
        self.static_bmp = bitmaps[0]
        self._static_size = self.static_bmp.Size
        self._static_padding = (10, 10)
        self._static_pos = wx.Point(self.GetPosition() + self._static_padding)

        self.handle_bmp = bitmaps[1]
        self._handle_size = self.handle_bmp.Size
        self._handle_centre = rect_centre(self._handle_size)
        self._handle_offset = (0, 0)  # x,y offset for positioning handle relative to the zero position and axis
        self._handle_default = wx.Point(0, 0)  # x,y co-ordinate
        self._handle_max_pos = wx.Point(self._static_size[0], self._static_size[1])  # max pos in relation to zero pos
        self._handle_pos = wx.Point(self._handle_offset)  # co-ordinate for actual position of handle

        self._switch_ticks = switch_ticks  # either int or list of ints
        self._ticklist = self.make_ticklist(self._switch_ticks)  # list of tick values (not wx.Points)
        self._curr_tick = 0  # ???
        self._tick_default = 0  # get rid of handle default???

        self._scroll_step = 1
        self._cursor_key_step = 1

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
        pad_x, pad_y = self._static_padding
        size = wx.Size(w + pad_x * 2, h + pad_y * 2)
        return size

    # Event handling #
    def on_paint(self, _):
        window_rect = self.GetRect()
        # print(window_rect)
        buffer_bitmap = self.parent.bg_render.GetSubBitmap(window_rect)
        self.draw_to_context(wx.BufferedPaintDC(self, buffer_bitmap))

    def draw_to_context(self, dc):
        dc.DrawBitmap(self.static_bmp, self._static_pos)
        if self.inverted:
            position = self._handle_max_pos[0] - self._handle_pos[0] + self._static_pos[0], \
                       self._handle_max_pos[1] - self._handle_pos[1] + self._static_pos[1]
        else:
            position = self._handle_pos[0] + self._static_pos[0], \
                       self._handle_pos[1] + self._static_pos[1]
        dc.DrawBitmap(self.handle_bmp, position)

        if self.highlight and self.HasFocus():
            self.draw_highlight(dc, self.GetSize(), self.highlight_box)

    def on_keypress(self, event):
        if self.HasFocus():
            keycode = event.GetKeyCode()
            index = vertical = self.vertical  # purely for readability
            inverted = self.inverted  # "
            if keycode in [wx.WXK_RIGHT, wx.WXK_UP]:
                if (inverted and not vertical) or (vertical and not inverted):
                    self.set_tick(self._curr_tick - self._cursor_key_step)
                else:
                    self.set_tick(self._curr_tick + self._cursor_key_step)
            elif keycode in [wx.WXK_LEFT, wx.WXK_DOWN]:
                if (inverted and not vertical) or (vertical and not inverted):
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
        vertical = self.vertical
        inverted = self.inverted
        delta = event.GetWheelDelta()  # usually +/-120, but it's better not to assume
        if (inverted and not vertical) or (vertical and not inverted):
            self.set_tick(self._curr_tick - self._scroll_step * event.GetWheelRotation() // delta)
        else:
            self.set_tick(self._curr_tick + self._scroll_step * event.GetWheelRotation() // delta)

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
        index = self.vertical
        position = mouse_pos[index] - self._handle_centre[index] - self._static_padding[index]
        closest_tick = min(range(len(self._ticklist)), key=lambda i: abs(self._ticklist[i] - position))
        if self.inverted:
            closest_tick = len(self._ticklist) - closest_tick - 1
        self.set_tick(closest_tick)

    def move_handle(self, pos):
        if self.vertical:
            self.set_position((self._handle_pos[0], pos))
        else:
            self.set_position((pos, self._handle_pos[1]))

    def on_middle_up(self, _):
        if not self.HasFocus():
            self.SetFocus()
        self.reset_position()

    def make_ticklist(self, ticks):
        tick_list = []
        index = self.vertical
        max_ = self._handle_max_pos[index]
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
        print(tick_list)
        return tick_list

    # Getters and Setters #
    def set_padding(self, padding=(0, 0)):
        """ Apply additional padding around the static image, mouse events will extend into the padding """
        self._static_padding = padding
        self._static_pos = self.GetPosition() + self._static_padding

    def set_max(self, pos=(0, 0)):
        """ Sets the co-ordinates for the maximum position """
        if 0 <= pos[0] <= self._static_size[0]:  # checks for less than zero and great than the image width
            if self._handle_max_pos != pos:
                self._handle_max_pos = pos
                self._ticklist = self.make_ticklist(self._switch_ticks)  # redo tick calculation
        else:
            raise ValueError('The position value is not within the boundary of the slider widget')

    def set_offset(self, pos=(0, 0)):
        if (0 <= pos[0] <= self._static_size[0]) and (0 <= pos[1] <= self._static_size[1]):
            self._handle_offset = pos
        else:
            raise ValueError('The position value is not within the boundary of the slider widget')

    def set_step(self, scroll=1, key=1):
        """ Set the increment value (in degrees) for the scroll-wheel and cursor keys"""
        self.set_scroll_step(scroll)
        self.set_key_step(key)

    def set_scroll_step(self, step=1):
        """ Set the scroll-wheel step size (int > 0) """
        self._scroll_step = step

    def set_key_step(self, step=1):
        """ Set cursor key step size (int > 0) """
        self._cursor_key_step = step

    def set_default_tick(self, tick=0):
        """ Set the default position for the handle, resetting will place the handle at this point"""
        if 0 <= tick < len(self._ticklist):  # make sure the tick value is within range
            self._tick_default = tick
            if self.vertical:
                self._handle_default = (self._handle_pos[0], self._ticklist[tick])
            else:
                self._handle_default = (self._ticklist[tick], self._handle_pos[1])
        else:
            raise ValueError('The tick value is not within range')

    def set_tick(self, tick):
        """ Validate and Set the tick value and the position for the handle """
        if tick < 0:  # make sure the tick value is within range - adjust if not
            tick = 0
        elif tick >= len(self._ticklist):
            tick = len(self._ticklist) - 1
        if tick != self._curr_tick:
            print(f'good - tick is{tick}')
            self._curr_tick = tick
            if self.vertical:
                self.set_position((self._handle_pos[0], self._ticklist[tick]))
            else:
                self.set_position((self._ticklist[tick], self._handle_pos[1]))
            wx.PostEvent(self, sss_cmd_event(id=self.GetId(), value=self.value))
            self.Refresh(True)

    def set_position(self, pos=(0, 0)):
        """ Parse and Set the (actual pixel) position for the handle """
        valid_pos = self._validate_limits(pos, self._handle_max_pos)
        if valid_pos != self._handle_pos:
            self._handle_pos = valid_pos
            self.Refresh(True)

    def reset_position(self, animate=True):
        self._animate(self._handle_default, animate)  # only use of handle_default - remove?

    # Properties #
    @property
    def value(self):
        return self._curr_tick  # index

    @value.setter
    def value(self, tick):
        self.set_tick(tick)

    # Helper methods #
    def _animate(self, destination, animate=True):
        if not animate:
            self.set_position(destination)
        else:
            index = self.vertical
            curr_pos = self._handle_pos[index]  # for horizontal movement, [1] for vertical...
            max_pos = self._handle_max_pos[index]
            def_pos = destination[index]
            diff = def_pos - curr_pos
            if diff:
                step = 4 * int(diff / abs(diff))
                for i in range(curr_pos, def_pos, step):
                    self.move_handle(i)
                    # because we are using sleep in a loop, we are not returning control to the main loop
                    # so we need to call update() to refresh the screen immediately - ie to 'animate'
                    self.Update()
                    if i != 0:
                        time.sleep(ptw.easeInQuart(abs((curr_pos - i + 1) / diff)) / int((max_pos - def_pos) * 0.75))
                        # TODO don't like sleeping the tween - threading version, maybe use position not time
                        # Also maybe extend function for clicking on a point animation
                self.set_tick(self._tick_default)

    def _validate_limits(self, position, max_pos):
        index = self.vertical
        if position[index] > max_pos[index]:
            return max_pos
        elif position[index] < 0:
            if self.vertical:
                return max_pos[0], 0
            else:
                return 0, max_pos[1]
        return position


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
