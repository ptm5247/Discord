from discord_app import QPainterPath

class RRect(QPainterPath):

  def __init__(
    self, x: float, y: float, w: float, h: float, rx=0., ry=0.
  ) -> None:
    super().__init__()
    self.addRoundedRect(x, y, w, h, rx, ry)

__all__ = ['RRect']
