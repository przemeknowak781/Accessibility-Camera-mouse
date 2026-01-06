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
        self.ControlType = None
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
    def test_pick_target_prefers_clickable_point(self):
        snapper = SmartSnapper()
        button = _Control(
            "ButtonControl",
            rect=None,
            clickable=(105, 110),
        )
        pane = _Control(
            "PaneControl",
            rect=_Rect(0, 0, 300, 300),
            children=[button],
        )
        button._parent = pane

        target = snapper._pick_target(pane, 100, 100, snap_radius=30)
        self.assertEqual(target, (105.0, 110.0))

    def test_pick_target_uses_child_center(self):
        snapper = SmartSnapper()
        button = _Control(
            "ButtonControl",
            rect=_Rect(100, 120, 140, 160),
        )
        pane = _Control(
            "PaneControl",
            rect=_Rect(0, 0, 300, 300),
            children=[button],
        )
        button._parent = pane

        target = snapper._pick_target(pane, 110, 130, snap_radius=50)
        self.assertEqual(target, (120.0, 140.0))


if __name__ == "__main__":
    unittest.main()
