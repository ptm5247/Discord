from typing import TypeVar

from discord_app import QSize, Qt, QLabel, QPushButton

T = TypeVar('T')

def create_elided_qwidget(for_type: type[T]) -> type[T]:
  class ElidedQWidget(for_type):

    def __init__(self, *args, **kwargs) -> None:
      super().__init__(*args, **kwargs)
      self.full_text = '' # should check args[0] here for QLabel
    
    def sizeHint(self) -> QSize:
      self.ensurePolished()
      return self.fontMetrics().size(0, self.full_text)

    def _elide_and_set_text(self) -> None:
      self.ensurePolished()
      elided = self.fontMetrics().elidedText(
        self.full_text, Qt.TextElideMode.ElideRight, self.width()
      )
      super().setText(elided)

    def resizeEvent(self, _) -> None:
      self._elide_and_set_text()
  
    def setText(self, a0: str) -> None:
      self.full_text = a0
      self._elide_and_set_text()
  return ElidedQWidget

ElidedQLabel      = create_elided_qwidget(QLabel)
ElidedQPushButton = create_elided_qwidget(QPushButton)

__all__ = ['ElidedQLabel', 'ElidedQPushButton']
