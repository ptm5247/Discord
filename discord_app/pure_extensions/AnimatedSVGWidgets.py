import regex

from math import sin, pi

from discord_app import QFile, QPushButton, QSvgWidget, QTime, QWidget

class ChannelDropdown(QSvgWidget):
  
  file = QFile('local:dropdown.svg')
  file.open(file.OpenModeFlag.ReadOnly)
  data = file.readAll().data()
  file.close()

  builder = regex.match(b'(.*<path.*?)(>.*)', data)

  def __init__(self, parent: QWidget) -> None:
    super().__init__(parent, exclude=['rotate'])

    self.load(self.data)
    center = self.renderer().viewBoxF().center()
    self.cx, self.cy = center.x(), center.y()

  def rotate(self, angle: str) -> None:
    self.load(self.builder.expand(bytes(
      rf'\1 transform="rotate({angle}, {self.cx}, {self.cy})"\2', 'utf-8'
    )))

class TypingBubbles(QSvgWidget):

  file = QFile('local:typing.svg')
  file.open(file.OpenModeFlag.ReadOnly)
  data = file.readAll().data()
  file.close()

  circle = b'(<circle.*?r=").*?(".*?opacity:\s*).*?(;.*?</circle>)'
  builder = regex.match(b'(.*?)' + circle * 3 + b'(.*)', data)
  template = r'\1\g<2>%f\g<3>%f\4\g<5>%f\g<6>%f\7\g<8>%f\g<9>%f\10\11'

  START_TIME = QTime.currentTime()
  LOOP_TIME_MS = 1200
  MAX_RADIUS = 3.5
  MIN_RADIUS = 2.8

  def __init__(self, parent: QWidget) -> None:
    super().__init__(parent)

    self.timer = None

    self.load(self.data)
    self.hide()
  
  def show(self) -> None:
    if self.timer is None:
      self.timer = self.startTimer(33)
    super().show()
  
  def hide(self) -> None:
    if self.timer:
      self.killTimer(self.timer)
      self.timer = None
    super().hide()

  def timerEvent(self, _) -> None:
    t = self.START_TIME.msecsTo(QTime.currentTime())
    phase = t % self.LOOP_TIME_MS
    params = []
    for _ in range(3):
      y = max(0, sin(phase / self.LOOP_TIME_MS * 2 * pi))
      params.append(self.MIN_RADIUS + (self.MAX_RADIUS - self.MIN_RADIUS) * y)
      params.append(0.3 + (1 - 0.3) * y)
      phase -= self.LOOP_TIME_MS / 6

    data = bytes(self.template % tuple(params), 'utf-8')
    self.load(self.builder.expand(data))

class SmallTypingBubbles(TypingBubbles):

  file = QFile('local:typing-small.svg')
  file.open(file.OpenModeFlag.ReadOnly)
  data = file.readAll().data()
  file.close()

  builder = regex.match(b'(.*?)' + TypingBubbles.circle * 3 + b'(.*)', data)

  MAX_RADIUS = 2.5
  MIN_RADIUS = 2.

class SvgPushButton(QPushButton):

  def __init__(self, file: str, parent: QWidget) -> None:
    super().__init__(parent)
    self.svg = QSvgWidget(file, self, name='Content')

  def resizeEvent(self, _) -> None:
    self.svg.setFixedSize(self.contentsRect().size())
    self.svg.move(self.contentsRect().topLeft())

  def paintEvent(self, _) -> None: ...

__all__ = [
  'ChannelDropdown', 'SvgPushButton', 'TypingBubbles', 'SmallTypingBubbles'
]
