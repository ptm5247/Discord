from discord_app import (
  DTextChannel, DDMChannel, DMessageable,
  Qt, QStackedLayout, QHBoxLayout, QWidget, QLabel, QSizePolicy, QVBoxLayout,
  QGridLayout,
  MultiShadow, qsignals
)

from . import ChatBox, TextChannelMenuBar, MemberList

class ChannelScreen(QWidget):
  
  def __init__(self, parent: QWidget) -> None:
    super().__init__(parent, layout=QStackedLayout)

    self.layout().addWidget(NoChannelScreen(self))
    self.layout().addWidget(TextChannelScreen(self))
    self.layout().addWidget(DMChannelScreen(self))

    qsignals.channel_selected.connect(self.channel_selected)

  # TODO move logic from NoChannelScreen and TextChannelScreen out here
  def channel_selected(self, channel: DMessageable | None) -> None:
    match channel:
      case None:           index = 0
      case DTextChannel(): index = 1
      case DDMChannel():   index = 2
      case _: raise ValueError(f'unsupported channel {channel}')
    self.layout().setCurrentIndex(index)

class NoChannelScreen(QWidget):

  def __init__(self, parent: QWidget) -> None:
    super().__init__(parent, layout=QVBoxLayout)

    image_container = QWidget(self, layout=QHBoxLayout)
    image = QLabel(image_container, name='Image')
    title = QLabel('NO TEXT CHANNELS', self, name='Title')
    subtitle = QLabel(
      "You find yourself in a strange place. You don't have access to any " +
      "text channels, or there are none in this server.", self, name='SubTitle'
    )

    title.setAlignment(Qt.AlignmentFlag.AlignHCenter)
    subtitle.setAlignment(Qt.AlignmentFlag.AlignHCenter)
    subtitle.setWordWrap(True)

    self.layout().addStretch()
    self.layout().addWidget(image_container)
    image_container.layout().addWidget(image)
    self.layout().addSpacing(40)
    self.layout().addWidget(title)
    self.layout().addSpacing(8)
    self.layout().addWidget(subtitle)
    self.layout().addStretch()
    self.layout().setAlignment(Qt.AlignmentFlag.AlignHCenter)

class TextChannelScreen(QWidget):

  def __init__(self, parent: QWidget) -> None:
    super().__init__(parent, layout=QGridLayout)

    self.menu_bar = TextChannelMenuBar(self)
    self.chat_box = ChatBox(self, DTextChannel)
    self.member_list = MemberList(self)

    self.layout().addWidget(self.menu_bar, 0, 0, 1, 2)
    self.layout().addWidget(self.chat_box, 1, 0)
    self.layout().addWidget(self.member_list, 1, 1, 2, 1)

    self.menu_bar.raise_()
    self.menu_bar.setGraphicsEffect(MultiShadow())
    self.menu_bar.controls.show_member_list.toggled.connect(
      self.show_member_list
    )
    self.chat_box.setSizePolicy(
      QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding
    )

  # TODO make state persist
  def show_member_list(self, show: bool) -> None:
    if show: self.member_list.show()
    else:    self.member_list.hide()

class DMChannelScreen(QWidget):

  def __init__(self, parent: QWidget) -> None:
    super().__init__(parent, layout=QGridLayout)

    # self.menu_bar = TextChannelMenuBar(self)
    self.chat_box = ChatBox(self, DDMChannel)
    # self.member_list = MemberList(self)

    # self.layout().addWidget(self.menu_bar, 0, 0, 1, 2)
    self.layout().addWidget(self.chat_box, 1, 0)
    # self.layout().addWidget(self.member_list, 1, 1, 2, 1)

    # self.menu_bar.raise_()
    # self.menu_bar.setGraphicsEffect(MultiShadow())
    # self.menu_bar.controls.show_member_list.toggled.connect(
    #   self.show_member_list
    # )
    self.chat_box.setSizePolicy(
      QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding
    )
