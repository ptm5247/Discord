from typing import Literal, NamedTuple

from discord_app import (
  QWidget, QGridLayout, QPoint, QLabel, QSize, QPointF, QPolygonF, QTransform,
  QPainter, QPainterPath, QRect, QColor, Qt
)

Anchor = Literal['top', 'right', 'bottom', 'left']

class TooltipSummons(NamedTuple):
  owner: QWidget
  anchor: Anchor
  text: str
  distance: int

class Tooltip(QWidget):

  DISTANCE = 3

  def __init__(self, parent: QWidget) -> None:
    super().__init__(parent.window(), layout=QGridLayout)

    self.owner: QWidget = None
    self.label = TooltipText(self)
    self.arrow = TooltipArrow(parent.window())

    self.label.setWordWrap(True)
    self.layout().addWidget(self.label)
    self.layout().setSizeConstraint(self.layout().SizeConstraint.SetFixedSize)

    self.hide()
    self.arrow.hide()
  
  def summon(self, summons: TooltipSummons | None):
    if summons:
      self.owner = summons.owner
      self.anchor = summons.anchor
      self.label.setFont(self.owner.font())
      self.label.setText(summons.text)
      pos = self.owner.mapTo(self.parentWidget(), QPoint())
      sw, sh = self.sizeHint().width, self.sizeHint().height
      ow, oh = self.owner.width, self.owner.height
      aw, ah = self.arrow.width, self.arrow.height
      d = self.DISTANCE + summons.distance
      match self.anchor:
        case 'top':
          self.arrow.set_rotation(270)
          pos += QPoint((ow() - sw()) // 2, -(sh() + ah() + d))
          apos = pos + QPoint((sw() - aw()) // 2, sh())
        case 'right':
          self.arrow.set_rotation(0)
          pos += QPoint(ow() + aw() + d, (oh() - sh()) // 2)
          apos = pos + QPoint(-aw(), (sh() - ah()) // 2)
        case 'bottom':
          self.arrow.set_rotation(90)
          pos += QPoint((ow() - sw()) // 2, oh() + ah() + d)
          apos = pos + QPoint((sw() - aw()) // 2, -ah())
        case 'left':
          self.arrow.set_rotation(180)
          pos += QPoint(-(sw() + aw() + d), (oh() - sh()) // 2)
          apos = pos + QPoint(sw(), (sh() - ah()) // 2)
        case _: raise ValueError(f'invalid anchor {self.anchor}')
      if (shift := self.parentWidget().width() - 12 - (pos.x() + sw())) < 0:
        pos += QPoint(shift, 0)
      self.move(pos)
      self.arrow.move(apos)
      self.show()
    else:
      self.hide()

  def raise_(self) -> None: super().raise_(); self.arrow.raise_()
  def show(self) -> None: self.raise_(); self.arrow.show(); super().show()
  def hide(self) -> None: self.arrow.hide(); super().hide()

class TooltipText(QLabel):

  def sizeHint(self) -> QSize:
    self.ensurePolished()
    metrics = self.fontMetrics()
    bound = QRect(0, 0, self.maximumWidth(), 0)
    rect = metrics.boundingRect(bound, Qt.TextFlag.TextWordWrap, self.text())
    expand = rect.height() > metrics.height() + 1
    return rect.size().expandedTo(QSize(self.maximumWidth() * expand, 0))
  
class TooltipArrow(QWidget):

  SIZE = 5
  ARROW = QPolygonF((QPointF(), QPointF(SIZE, -SIZE), QPointF(SIZE, SIZE)))

  def set_rotation(self, rotation: float) -> None:
    self.arrow: QPolygonF = self.ARROW * QTransform().rotate(rotation)
    self.arrow.translate(-self.arrow.boundingRect().topLeft())
    self.setFixedSize(self.arrow.boundingRect().size().toSize())

  def paintEvent(self, _) -> None:
    path = QPainterPath()
    path.addPolygon(self.arrow)
    painter = QPainter(self)
    painter.fillPath(path, QColor(17, 18, 20))

__all__ = ['Tooltip', 'TooltipSummons']
