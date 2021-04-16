class Padding:
    """
    Padding can be applied to the foundation element of an ActiveImageControl

    :param widths:  take a tuple of 1 to 4 integers or None
                    ()          None will reset_position padding to 0 on all sides
                    (10,)       All four sides are padded 10px
                    (10,20)     Top and bottom are padded 10px; Right and left are padded 20px
                    (10,5,20)   Top padding 10px; right and left are 5px; bottom padding is 20px
                    (5,10,15,8) Top padding 5px; right 10px; bottom 15px; left 8px
                                Top; Right; Bottom; Left - mimics the common CSS pattern
    """

    def __init__(self, widths=tuple( (0, 0, 0, 0) )):
        Self.padding = make_padding(widths)


def make_padding(widths=tuple( (0, 0, 0, 0) )):
    """ returns a tuple of 4 integers representing the amount of padding-> Top; Right; Bottom; Left """
    length = len(widths)
    if length < 5:
        if length == 1:
            p = widths[0]
            padding = (p, p, p, p)
        elif length == 2:
            tb, rl = widths
            padding = (tb, rl, tb, rl)
        elif length == 3:
            t, rl, b = widths
            padding = (t, rl, b, rl)
        else:
            padding = tuple(widths)
    else:
        raise ValueError('Too many values passed: 1 - 4 are expected')
    return padding
