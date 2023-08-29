from discord_app import (
  QWidget, QHBoxLayout, QLabel, QSizePolicy as QSP, Qt, ElidedQPushButton,
  QPushButton, QVBoxLayout, QFontMetrics, QTextOption, ScrollArea,
  SvgPushButton, QPoint,
  DTextChannel, DMessageableChannel, DGuildChannel,
  qsignals, dsignals, ui
)

import discord_app._utils as utils

class TextChannelMenuBar(QWidget):
  
  def __init__(self, parent: QWidget) -> None:
    super().__init__(parent, layout=QHBoxLayout)

    self.channel: DTextChannel = None

    self.icon = QLabel(self, name='ChannelIcon')
    self.name = QLabel(self)
    self.name.setSizePolicy(QSP.Policy.Maximum, QSP.Policy.Preferred)
    self.topic_container = QWidget(self, layout=QHBoxLayout)
    self.topic_container.setSizePolicy(QSP.Policy.Ignored, QSP.Policy.Preferred)
    self.topic_divider = QLabel(self.topic_container, name='TopicDivider')
    self.topic = ElidedQPushButton(self.topic_container, name='ChannelTopic')
    self.topic.setSizePolicy(QSP.Policy.Ignored, QSP.Policy.Preferred)
    self.topic.clicked.connect(self.show_topic_popup)
    self.controls = MenuBarControls(self)
    self.controls_placeholder = QWidget(self)
    self.controls_placeholder.setAttribute(
      Qt.WidgetAttribute.WA_TransparentForMouseEvents
    )

    self.layout().addWidget(self.icon)
    self.layout().addWidget(self.name)
    self.layout().addWidget(self.topic_container)
    self.topic_container.layout().addWidget(self.topic_divider)
    self.topic_container.layout().addWidget(self.topic)
    self.layout().addWidget(self.controls_placeholder)

    qsignals.channel_selected.connect(self.channel_selected)
    # dsignals.on_guild_channel_icon_update.connect(self.guild_channel_icon_update)
    # dsignals.on_guild_channel_name_update.connect(self.guild_channel_name_update)
    # dsignals.on_guild_channel_topic_update.connect(self.guild_channel_topic_update)
  
  def resizeEvent(self, _) -> None:
    shift = self.controls.width() + self.layout().contentsMargins().right()
    self.controls.move(self.rect().topRight() - QPoint(shift, 0))

  def channel_selected(self, channel: DMessageableChannel | None) -> None:
    if isinstance(channel, DTextChannel):
      self.channel = channel
      self.guild_channel_icon_update(channel)
      self.guild_channel_name_update(channel)
      self.guild_channel_topic_update(channel)
  
  def guild_channel_icon_update(self, channel: DGuildChannel) -> None:
    if channel is self.channel:
      file_name, _ = utils.get_icon_type(channel)
      self.icon.style('image', file_name)

  def guild_channel_name_update(self, channel: DGuildChannel) -> None:
    if channel is self.channel:
      self.name.setText(channel.name)
  
  def guild_channel_topic_update(self, channel: DGuildChannel) -> None:
    if channel is self.channel:
      if self.channel.topic:
        self.topic.setText(' '.join(self.channel.topic.split()))
        self.topic_divider.show()
        self.topic.show()
      else:
        self.topic_divider.hide()
        self.topic.hide()
  
  def show_topic_popup(self) -> None:
    ui.show_popup(TopicPopup(self))

class MenuBarControls(QWidget):

  def __init__(self, parent: TextChannelMenuBar) -> None:
    super().__init__(parent, layout=QHBoxLayout)

    self.layout().setSizeConstraint(QHBoxLayout.SizeConstraint.SetFixedSize)
    self.fade = QWidget(self, name='ControlsFade')
    self.show_member_list = QPushButton(self, name='ShowMemberList')
    self.show_member_list.setCheckable(True)
    self.show_member_list.toggle()

    self.layout().addWidget(self.fade)
    self.layout().addWidget(self.show_member_list)

  def resizeEvent(self, _) -> None:
    menu: TextChannelMenuBar = self.parentWidget()
    menu.controls_placeholder.setFixedWidth(self.width() - self.fade.width())

class TopicPopup(QWidget):

  def __init__(self, parent: TextChannelMenuBar) -> None:
    super().__init__(parent, layout=QVBoxLayout)
    self.setSizePolicy(QSP.Policy.Preferred, QSP.Policy.Maximum)

    title_container = QWidget(self, layout=QHBoxLayout, name='TitleContainer')
    title = QLabel('#' + parent.channel.name, self, name='Title')
    close = SvgPushButton('local:close.svg', self)
    close.clicked.connect(ui.popup_window.click)
    scroll_area = ScrollArea(self, hide_scrollbar=False)
    content = QLabel(self, name='Topic')
    content.ensurePolished()
    content.setText(self.wrap_to(
      parent.channel.topic, content.fontMetrics(), content.width()
    ))

    self.layout().addWidget(title_container)
    title_container.layout().addWidget(title)
    title_container.layout().addWidget(close)
    self.layout().addWidget(scroll_area)
    scroll_area._layout().addWidget(content)

  @staticmethod
  def wrap_to(text: str, font_metrics: QFontMetrics, width: int) -> str:
    option = QTextOption()
    line_width = last = line_word_count = 0
    wrapped = ''
    space_width = font_metrics.horizontalAdvance(' ', option)
    while last < len(text):
      next = text.find(' ', last)
      if next == -1: next = len(text)
      newline = text.find('\n', last, next)
      if newline != -1:
        next = newline
      word = text[last:next]
      word_width = font_metrics.horizontalAdvance(word, option)
      if line_width + word_width <= width:
        if newline == next:
          line_width = line_word_count = 0
          wrapped += word + '\n'
        else:
          line_width += word_width + space_width
          line_word_count += 1
          wrapped += word + ' '
        last = next + 1
      elif line_word_count != 0:
        wrapped += '\n'
        line_word_count = line_width = 0
      else:
        part_width = part_end = 0
        while part_width <= width:
          part_width += font_metrics.horizontalAdvance(word[part_end], option)
          part_end += 1
        wrapped += word[:part_end - 1] + '\n'
        last += part_end - 1
    return wrapped
