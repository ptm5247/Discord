from discord_app import (
  Qt, QSize, pyqtSignal, QWheelEvent, QTransform, QPainter, QPainterPath, 
  QResizeEvent, QWidget, QHBoxLayout, QVBoxLayout, QScrollBar
)

# TODO drag then scroll does not work
# TODO resizing doesnt properly update the scrollbar position

class ScrollBar(QScrollBar):

  def __init__(self,
    parent: 'ScrollArea',
    width: int,
    hide_on_leave: bool
  ) -> None:
    super().__init__(parent)
    self.setFixedWidth(2 * width)
    self.setStyleSheet(self.styleSheet() + ' '.join([
      self.__class__.__qualname__, '{',
      f'border-radius: {width // 2}px;',
      f'margin: {width // 2}px;',
    '}']))
    self._scroll_area = parent
    self._bar_width = width
    self._hide_on_leave = hide_on_leave
    self._hidden = hide_on_leave
    self.setRange(0, 1000)

  def _enter(self) -> None:
    self._hidden = False
    self.update()

  def _leave(self) -> None:
    self._hidden = self._hide_on_leave
    self.update()

  def paintEvent(self, _) -> None:
    height_ratio = self._scroll_area._get_height_ratio()
    self.setPageStep(int(1000 * height_ratio))
    if not self._hidden and height_ratio < 1:
      height = (self.height() - self._bar_width) * height_ratio * .8
      y = self._bar_width / 2 + (self.height() - self._bar_width - height) * \
        self.sliderPosition() / self.maximum()
      path = QPainterPath()
      path.addRoundedRect(
        self._bar_width / 2, y, self._bar_width, height,
        self._bar_width / 2, self._bar_width / 2
      )
      painter = QPainter(self)
      painter.setRenderHint(QPainter.RenderHint.Antialiasing)
      painter.fillPath(path, 0x1A1B1E)

# a scroll area with no scrollbar and smooth scrolling
class ScrollArea(QWidget):

  ACCELERATION_MAGNITUDE = 3
  MAX_VELOCITY_MAGNITUDE = 160
  TIME_STEP_MS = 4
  UNIT_SCALE = 1000 / TIME_STEP_MS
  STOP_TIME_SEC = .2
  ANGLE_DELTA_SCALE_FACTOR = .75

  class Content(QWidget):
    set_height = pyqtSignal(int, int)
    def resizeEvent(self, event: QResizeEvent) -> None:
      self.set_height.emit(event.oldSize().height(), event.size().height())

  def __init__(
    self, parent: QWidget, hide_scrollbar=True, lock_to_bottom=False
  ) -> None:
    super().__init__(parent, layout=QHBoxLayout)

    self._view = QWidget(self)
    self.layout().addWidget(self._view)
    self._content = self.Content(self._view, layout=QVBoxLayout, name='Content')
    self._scroll_bar = None
    self._scroll_bar_width = 0
    if hasattr(self.__style__, 'scrollbar-width'):
      self._scroll_bar_width = getattr(self.__style__, 'scrollbar-width')
      self.add_scroll_bar(self._scroll_bar_width, hide_scrollbar)
    self.lock_to_bottom = lock_to_bottom
    self._content.set_height.connect(self.content_height_changed)

    # allows the box to change size when items are added later
    self._content.layout() \
      .setSizeConstraint(QVBoxLayout.SizeConstraint.SetFixedSize)

    self.timer_id = None
    self.clear()

  def content_height_changed(self, old_height: int, new_height: int) -> None:
    if self.lock_to_bottom:
      if old_height + self.content_y <= self._view.height() \
        and new_height + self.content_y > self._view.height():
        if self._scroll_bar:
          self._scroll_bar.setSliderPosition(1000)
        self.handle_manual_scroll(1000)
        self._ensure_still()
    if new_height + self.content_y < self.height():
      self._place_content(min(self.height() - self._content.height(), 0))

  def sizeHint(self) -> QSize:
    return self._content.sizeHint() + QSize(self._scroll_bar_width, 0)

  def _layout(self) -> QVBoxLayout:
    return self._content.layout()

  def add_scroll_bar(self, width: int, hide_on_leave=True) -> None:
    self._scroll_bar = ScrollBar(self, width // 2, hide_on_leave)
    self.layout().addWidget(self._scroll_bar)
    self._scroll_bar.sliderMoved.connect(self.handle_manual_scroll)

  def clear(self) -> None:
    while self._content.layout():
      if widget := self._content.layout().takeAt(0).widget():
        widget.deleteLater()
    self._place_content(0)
    self._ensure_still()

  # ensure the timer is off, v=0, and the destination is the current position
  def _ensure_still(self):
    self.velocity = 0
    self.destination = self.content_y
    if self.timer_id:
      self.timer_id = self.killTimer(self.timer_id)

  def handle_manual_scroll(self, value: int):
    self.content_y = int(self._get_min_height() * value / 1000)
    self._content.move(0, self.content_y)

  # scroll the content to the given position
  def _place_content(self, y: int) -> None:
    self.content_y = y
    self._content.move(0, self.content_y)
    if self._scroll_bar:
      self._scroll_bar.setSliderPosition(int(1000 * self._get_position_ratio()))

  # adjust the given point based on the content location
  def content_transform(self) -> QTransform:
    return QTransform.fromTranslate(0, self.content_y)
  
  def _get_min_height(self) -> int:
    return min(0, self._view.height() - self._content.height())
  
  def _get_position_ratio(self) -> float:
    min_y = self._get_min_height()
    return min_y and self.content_y / min_y
  
  def _get_height_ratio(self) -> float:
    return self._content.height() and \
      self._view.height() / self._content.height()
  
  def enterEvent(self, _) -> None:
    if self._scroll_bar:
      self._scroll_bar._enter()

  def leaveEvent(self, _) -> None:
    if self._scroll_bar:
      self._scroll_bar._leave()
  
  # capture mouse scrolling and schedule actual scrolling ticks
  def wheelEvent(self, a0: QWheelEvent) -> None:
    min_y = self._get_min_height()
    # don't scroll if content fits in the current window
    if min_y < 0:
      delta = a0.angleDelta().y() * self.ANGLE_DELTA_SCALE_FACTOR
      self.destination += int(delta)
      self.destination = min(0, max(min_y, self.destination))
    # schedule scrolling ticks
    if self.content_y != self.destination and not self.timer_id:
      self.timerEvent(None) # the timer does not call it immediately
      self.timer_id = self.startTimer(
        self.TIME_STEP_MS, Qt.TimerType.PreciseTimer
      )
    
  # automatically scroll when resizing reveals fillable space
  def resizeEvent(self, _) -> None:
    self._ensure_still()
    if self._content.height() + self.content_y < self.height():
      self._place_content(min(self.height() - self._content.height(), 0))

  # a single tick of the smooth scrolling
  def timerEvent(self, _) -> None:
    delta = self.destination - self.content_y
    if delta: # since it is sometimes 0
      sign = delta // abs(delta)
      # .5at^2 + vt
      stop_distance = int(
        self.STOP_TIME_SEC * self.UNIT_SCALE * \
        (abs(self.velocity) - self.STOP_TIME_SEC * self.ACCELERATION_MAGNITUDE)
      )
      # slow down if approaching destination, otherwise speed up
      self.velocity += (-1 if abs(delta) < stop_distance else 1) * \
        self.ACCELERATION_MAGNITUDE * sign
      # cap the velocity before changing position
      if (abs(self.velocity) > self.MAX_VELOCITY_MAGNITUDE):
        self.velocity = self.MAX_VELOCITY_MAGNITUDE * sign
      self.content_y += self.velocity
      # correct overshooting of the destination
      if delta * (self.destination - self.content_y) < 0:
        self.content_y = self.destination
        self.velocity = delta
      self._place_content(self.content_y)

    # ensure timer is off and params are as expected once destination is reached
    if self.content_y == self.destination:
      self._ensure_still()

__all__ = ['ScrollArea']
