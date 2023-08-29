from discord_app import QGraphicsEffect, QColor, QRectF, QPainter

class MultiShadow(QGraphicsEffect):

  COLORS = [QColor(2, 2, 2, 51), QColor(6, 6, 7, 13), QColor(2, 2, 2, 13)]

  def boundingRectFor(self, rect: QRectF) -> QRectF:
    return rect.adjusted(0, 0, 0, 2)

  def draw(self, painter: QPainter) -> None:
    a = self.sourceBoundingRect().bottomLeft()
    b = self.sourceBoundingRect().bottomRight()
    pixmap, offset = self.sourcePixmap()
    painter.drawPixmap(offset, pixmap)
    for color in self.COLORS:
      painter.setPen(color)
      painter.drawLine(a, b)
      a.setY(a.y() + .5)
      b.setY(b.y() + .5)

__all__ = ['MultiShadow']
