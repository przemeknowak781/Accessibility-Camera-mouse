import unittest

from src.smart_snap import SmartSnapper


class _Rect:
    def __init__(self, left, top, right, bottom):
        self.left = left
        self.top = top
        self.right = right
        self.bottom = bottom


class _Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y


class _Control:
    def __init__(
        self,
        control_type,
        rect=None,
        clickable=None,
        parent=None,
        children=None,
    ):
        self.ControlTypeName = control_type
        self.BoundingRectangle = rect
        self._clickable = clickable
        self._parent = parent
        self._children = children or []

    def GetClickablePoint(self):
        if self._clickable is None:
            return None
        return _Point(*self._clickable)

    def GetParentControl(self):
        return self._parent

    def GetChildren(self):
        return list(self._children)


class SmartSnapperTests(unittest.TestCase):
    def test_pick_interactive_uses_clickable_point_distance(self):
        snapper = SmartSnapper()
        button = _Control(
            "Button",
            rect=None,
            clickable=(105, 110),
        )
        pane = _Control(
            "Pane",
            rect=_Rect(0, 0, 300, 300),
            children=[button],
        )
        button._parent = pane

        picked = snapper._pick_interactive(pane, 100, 100, snap_radius=30)
        self.assertIs(picked, button)


if __name__ == "__main__":
    unittest.main()
