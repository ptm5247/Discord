import csv
import regex

from concurrent.futures import Future
from datetime import date
from discord.utils import utcnow
from os import makedirs

from discord_app import (
  QWidget, pyqtSignal, QVBoxLayout, QResizeEvent, Qt, QLabel,
  QSizePolicy as QSP, QHBoxLayout, QPainter, QPainterPath, QPoint, QTextOption,
  QGridLayout, QPushButton, QSize, QNetworkAccessManager, QPixmap, QDir,
  QNetworkRequest, QImageReader, QUrl, QBrush,
  DMessage, DMessageableChannel, DTextChannel, DDMChannel, DUser, DMember,
  DRawReactionActionEvent, DPartialEmoji, DReaction, DEmbed, DEmbedProxy,
  DAttachment,
  ScrollArea, TypingBubbles, RoundedIconMixin,
  root, qsignals, dsignals, state, client, registrar
)

# TODO only allow one instance
class ChatBox(QWidget):

  messages_available_ = pyqtSignal(object, list)
  set_width = pyqtSignal(int) # TODO sus

  def __init__(
    self, parent: QWidget, channel_type: type[DMessageableChannel]
  ) -> None:
    super().__init__(parent, layout=QVBoxLayout)

    self.channel_type = channel_type
    self.message_view = \
      ScrollArea(self, hide_scrollbar=False, lock_to_bottom=True)
    self.last_message: DMessage | None=None
    self.typing_zone = TypingZone(self)

    self.layout().addWidget(self.message_view)
    self.layout().addWidget(self.typing_zone)

    qsignals.channel_selected.connect(self.channel_selected)
    dsignals.on_message.connect(self.on_message)
    self.messages_available_.connect(self.messages_available)
    dsignals.on_raw_reaction_add.connect(self.on_raw_reaction_action)
    dsignals.on_raw_reaction_remove.connect(self.on_raw_reaction_action)
  
  def resizeEvent(self, event: QResizeEvent) -> None:
    if event.oldSize().width() != event.size().width():
      self.set_width.emit(self.width() - self.message_view._scroll_bar_width)
  
  def channel_selected(self, channel: DMessageableChannel | None) -> None:
    self.message_view.clear()
    if isinstance(channel, self.channel_type):
      client.submit(self.request_messages(channel))
      self.typing_zone.channel_id = channel.id
      self.typing_zone.typing_registry_update()

  async def request_messages(self, channel: DTextChannel | DDMChannel) -> None:
    messages = [m async for m in channel.history(limit=50)]
    self.messages_available_.emit(channel, messages)

  def messages_available(
    self, channel: DTextChannel | DDMChannel, messages: list[DMessage]
  ) -> None:
    if channel == state.selected_channel:
      for message in reversed(messages):
        self._message(message)
  
  def on_message(self, message: DMessage) -> None:
    if isinstance(message.channel, self.channel_type):
      if message.channel == state.selected_channel:
        self._message(message)

  def _message(self, message: DMessage) -> None:
    width = self.width() - self.message_view._scroll_bar_width
    last = self.last_message
    date = message.created_at.astimezone().date()
    date_gap = last is None or last.created_at.astimezone().date() != date
    starts_group = date_gap or message.author is not last.author \
      or (message.created_at - last.created_at).total_seconds() > 300
    widget = Message(self, message, starts_group, date_gap)
    if date_gap:
      date_header = DateHeader(self, date)
      self.message_view._layout().addWidget(date_header)
      date_header.set_width(width)
    self.message_view._layout().addWidget(widget)
    widget.set_width(width)
    self.last_message = message

  def get_message(self, message_id: int) -> 'Message | None':
    return self.message_view._content.findChild(
      Message, hex(message_id), Qt.FindChildOption.FindDirectChildrenOnly
    )
  
  def on_raw_reaction_action(self, payload: DRawReactionActionEvent) -> None:
    if payload.channel_id == state.selected_channel.id:
      if message := self.get_message(payload.message_id):
        client.submit(self.fetch_reaction(message, payload.emoji))
  
  async def fetch_reaction(
    self, message_widget: 'Message', emoji: DPartialEmoji
  ) -> None:
    channel = client.get_channel(message_widget.message.channel.id)
    message = await channel.fetch_message(message_widget.message.id)
    message_widget.accessories.reactions_update.emit(message.reactions)
  
class DateHeader(QWidget):

  def __init__(self, parent: ChatBox, date: date) -> None:
    super().__init__(parent, layout=QVBoxLayout)

    self.line = QWidget(self, name='DateLine')
    text = f'{date.strftime("%B")} {date.day}, {date.year}'
    label = QLabel(text, self, name='DateHeader')
    self.layout().setAlignment(Qt.AlignmentFlag.AlignHCenter)
    label.setSizePolicy(QSP.Policy.Preferred, QSP.Policy.Preferred)

    self.layout().addStretch(1)
    self.layout().addWidget(label)

    parent.set_width.connect(self.set_width)

  def set_width(self, width: int) -> None:
    self.setFixedWidth(width)
    self.line.setFixedWidth(width)

class Message(QWidget):

  def __init__(
    self, parent: ChatBox, message: DMessage,
    starts_group: bool, first_of_the_day: bool
  ) -> None:
    super().__init__(parent, layout=QVBoxLayout)
    self.setObjectName(hex(message.id))

    self.message = message
    created_at = message.created_at.astimezone()
    timestamp = created_at.strftime('%I:%M %p').lstrip('0')
    if starts_group:
      self.style('margin-top', '11px' if first_of_the_day else '17px')
      header = QWidget(self, layout=QHBoxLayout, name='Header')
      author = registrar.\
        Username(header, message.author, message.channel, False, True)
      today, stamp = utcnow().astimezone().date(), created_at.date()
      datestamp = 'Today at' if stamp == today \
         else 'Yesterday at' if (today - stamp).days == 1 \
         else stamp.strftime('%m/%d/%Y')
      timestamp = QLabel(f'{datestamp} {timestamp}', header, name='Timestamp')
      header.layout().addWidget(author)
      header.layout().addWidget(timestamp)
      header.layout().addStretch(1)
      self.layout().addWidget(header)
      Avatar(self, message.author)
    else:
      alignment = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignCenter
      QLabel(timestamp, self, name='Timestamp').setAlignment(alignment)

    self.pad = self.layout().contentsMargins().right() \
             + self.layout().contentsMargins().left()
    
    self.content = Content(message.content, self)
    self.accessories = MessageAccessories(self, message)

    self.layout().addWidget(self.content)
    self.layout().addWidget(self.accessories)

    parent.set_width.connect(self.set_width)
  
  def set_width(self, width: int) -> None:
    if self.content:
      self.content.setFixedWidth(width - self.pad)
    self.accessories.setFixedWidth(width - self.pad)
  
class Avatar(QWidget):

  def __init__(self, parent: QWidget, source: DUser | DMember) -> None:
    super().__init__(parent)
    self.brush = registrar.AssetBrush(self, source)
    self.path = QPainterPath()
    self.path.addEllipse(self.rect().toRectF())
  
  def paintEvent(self, _) -> None:
    painter = QPainter(self)
    painter.setRenderHint(painter.RenderHint.Antialiasing)
    painter.setRenderHint(painter.RenderHint.SmoothPixmapTransform)
    painter.fillPath(self.path, self.brush)

class Content(QWidget):

  def __init__(self, content: str, parent: QWidget) -> None:
    super().__init__(parent)

    self.renderer = MessageRenderer(self, content)

    if not content:
      self.hide()
  
  def hasHeightForWidth(self) -> bool: return True
  def heightForWidth(self, width: int) -> int:
    return self.renderer.height_for_width(width)

  def paintEvent(self, _) -> None:
    painter = QPainter(self)
    metrics = self.fontMetrics()
    cursor = QPoint(0, metrics.ascent())
    label_offset = -cursor
    option = QTextOption()
    for line in self.renderer.lines:
      line_height = metrics.height() + 1
      for fragment in line:
        if isinstance(fragment, QLabel):
          fragment.move(cursor + label_offset)
          cursor += QPoint(fragment.width(), 0)
          line_height = max(line_height, fragment.height())
        else:
          painter.drawText(cursor, fragment)
          cursor += QPoint(metrics.horizontalAdvance(fragment, option), 0)
      cursor = QPoint(0, cursor.y() + line_height)

class MessageAccessories(QWidget):

  reactions_update = pyqtSignal(list)

  def __init__(self, parent: QWidget, message: DMessage) -> None:
    super().__init__(parent, layout=QGridLayout)
    self.layout().setAlignment(Qt.AlignmentFlag.AlignLeft)

    for attachment_ in message.attachments:
      self.add_attachment(attachment_)

    for embed_ in message.embeds:
      embed = Embed(self, embed_)
      self.layout().addWidget(embed)
    
    self.reactions = QWidget(self, layout=QHBoxLayout, name='Reactions')
    self.reactions.layout().setAlignment(Qt.AlignmentFlag.AlignLeft)
    self.layout().addWidget(self.reactions)
    self.reactions.hide()
    self.reactions_update.connect(self.reaction_count_update)
    if message.reactions:
      self.reactions_update.emit(message.reactions)
  
  def add_attachment(self, attachment: DAttachment) -> None:
    if content_type := attachment.content_type:
      if content_type.startswith('image/'):
        widget = ImageRenderer(self, attachment)
      else:
        widget =  QLabel(f'unsupported content type: {content_type}', self)
    else:
      widget = QLabel('attachment has no content type...', self)
    self.layout().addWidget(widget)
  
  def reaction_count_update(self, reactions: list[DReaction]) -> None:
    self.reactions.show() if reactions else self.reactions.hide()
    i = -1
    for i, reaction in enumerate(reactions):
      widget = None
      while item := self.reactions.layout().itemAt(i):
        widget: Reaction = item.widget()
        if widget.reaction == reaction: break
        self.reactions.layout().takeAt(i)
        widget.deleteLater()
      if widget:
        widget.count.setText(str(reaction.count))
      else:
        self.reactions.layout().addWidget(Reaction(self.reactions, reaction))
    i += 1
    while item := self.reactions.layout().takeAt(i):
      item.widget().deleteLater()

class Embed(QWidget):

  def __init__(self, parent: QWidget, embed: DEmbed) -> None:
    super().__init__(parent, layout=QHBoxLayout)
    self.layout().setAlignment(Qt.AlignmentFlag.AlignLeft)

    border = QWidget(self, name='Border')
    border.style('background', embed.color)
    content = QWidget(self, layout=QVBoxLayout, name='Content')
    content.setSizePolicy(QSP.Policy.Minimum, QSP.Policy.Preferred)
    self.layout().addWidget(border)
    self.layout().addWidget(content)

    if embed.title:
      title = QLabel(embed.title, self, name='Title')
      title.setWordWrap(True)
      content.layout().addWidget(title)
    if embed.description:
      description = QLabel(embed.description, self, name='Description')
      description.setWordWrap(True)
      content.layout().addWidget(description)
    if embed.thumbnail.proxy_url:
      thumbnail = ImageRenderer(self, embed.thumbnail)
      content.layout().addWidget(thumbnail)
    if embed.footer.text:
      footer = QLabel(embed.footer.text, self, name='Footer')
      footer.setWordWrap(True)
      content.layout().addWidget(footer)

class Reaction(QPushButton):

  def __init__(self, parent: QWidget, reaction: DReaction) -> None:
    super().__init__(parent, layout=QHBoxLayout)
    self.setCheckable(True)

    self.reaction = reaction
    self.message = reaction.message
    if isinstance(reaction.emoji, str):
      label = MessageRenderer.parse_content(reaction.emoji, self)[0]
      label.setFixedSize(16, 16)
      self.layout().addWidget(label)
    self.count = QLabel(str(reaction.count), self)
    self.count.setAlignment(Qt.AlignmentFlag.AlignCenter)
    self.layout().addWidget(self.count)
    self.layout().setSizeConstraint(QHBoxLayout.SizeConstraint.SetFixedSize)

    if reaction.me: self.setChecked(True)
    self.toggled.connect(self.react)

  def react(self, toggled: bool) -> None:
    if toggled:
      coro = self.message.add_reaction(self.reaction)
    else:
      coro = self.message.remove_reaction(self.reaction, client.user)
    client.submit(coro)

class TypingZone(QWidget):

  def __init__(self, parent: QWidget) -> None:
    super().__init__(parent, layout=QHBoxLayout)
    self.layout().setAlignment(Qt.AlignmentFlag.AlignLeft)

    self.bubbles = TypingBubbles(self)
    self.channel_id = None
    self.label = QLabel(self)

    self.layout().addWidget(self.bubbles)
    self.layout().addWidget(self.label)
    qsignals.typing_registry_update.connect(self.typing_registry_update)

  def typing_registry_update(self) -> None:
    users = list(map(
      lambda s: f'<strong>{s}</strong>',
      filter(None, state.typing_by_id.get(self.channel_id, {}))
    ))
    if len(users) == 0:
      self.bubbles.hide()
      self.label.hide()
    else:
      if len(users) == 1:
        text = f'{users[0]} is typing...'
      elif len(users) == 2:
        text = f'{users[0]} and {users[1]} are typing...'
      elif len(users) == 3:
        text = f'{users[0]}, {users[1]}, and {users[2]} are typing...'
      else:
        text = 'Several people are typing...'
      self.bubbles.show()
      self.label.setText(text)
      self.label.show()

class MessageRenderer:

  mapping_file = root.absoluteFilePath('emoji-mapping.csv')
  with open(mapping_file, encoding='utf-8') as file:
    reader = csv.reader(file)
    emoji_mapping = {line[0]: (line[1], line[2]) for line in reader}
  grapheme_splitter = regex.compile(r'\X')
  option = QTextOption()

  def __init__(self, parent: QWidget, content: str) -> None:
    self.content = self.parse_content(content, parent)
    parent.ensurePolished()
    self.metrics = parent.fontMetrics()
    self.text_line_height = self.metrics.height() + 1
    self.space_width = self.metrics.horizontalAdvance(' ', self.option)
    self.limited = True
  
  def init_params(self, width: int) -> None:
    self.lines: list[list[QLabel | str]] = []
    self.height = 0
    self.width = width

    self.line: list[QLabel | str] = []
    self.limited = False
    self.max_line_width = 0
    self.line_width = 0
    self.line_height = self.text_line_height

    self.word = ''
    self.word_width = 0
    self.text_fragment = ''
  
  def append_grapheme(self, grapheme: str) -> None:
    grapheme_width = self.metrics.horizontalAdvance(grapheme, self.option)
    if self.word_width + grapheme_width > self.width:
      self.terminate_word()
    self.word += grapheme
    self.word_width += grapheme_width

  def append_word(self, word: str, word_width: int) -> None:
    if self.line_width + word_width > self.width:
      self.limited = True
      self.terminate_text_fragment()
      self.terminate_line()
    self.text_fragment += word
    self.line_width += word_width
  
  def append_space(self) -> None:
    self.text_fragment += ' '
    self.line_width += self.space_width
    if self.line_width > self.width:
      self.limited = True
      self.terminate_text_fragment()
      self.terminate_line()
  
  def append_emoji(self, emoji: QLabel) -> None:
    if self.line_width + emoji.width() > self.width:
      self.limited = True
      self.terminate_line()
    self.line.append(emoji)
    self.line_width += emoji.width()
    self.line_height = max(self.line_height, emoji.height())
  
  def terminate_word(self) -> None:
    self.append_word(self.word, self.word_width)
    self.word = ''
    self.word_width = 0
  
  def terminate_text_fragment(self) -> None:
    self.line.append(self.text_fragment)
    self.text_fragment = ''
  
  def terminate_line(self) -> None:
    self.lines.append(self.line)
    self.height += self.line_height
    self.line = []
    self.max_line_width = max(self.max_line_width, self.line_width)
    self.line_width = 0
    self.line_height = self.text_line_height

  def height_for_width(self, width: int) -> int:
    if not self.limited and width >= self.max_line_width:
      return self.height
    else:
      self.init_params(width)
      for fragment in self.content:
        if isinstance(fragment, QLabel):
          if self.word:          self.terminate_word()
          if self.text_fragment: self.terminate_text_fragment()
          self.append_emoji(fragment)
        else:
          for match in self.grapheme_splitter.finditer(fragment):
            grapheme = fragment[slice(*match.span())]
            if grapheme == ' ':
              if self.word: self.terminate_word()
              self.append_space()
            elif grapheme == '\n':
              if self.word:          self.terminate_word()
              if self.text_fragment: self.terminate_text_fragment()
              self.terminate_line()
            else:
              self.append_grapheme(grapheme)
      if self.word:          self.terminate_word()
      if self.text_fragment: self.terminate_text_fragment()
      self.terminate_line()
      return self.height
  
  @classmethod
  def parse_content(cls, content: str, parent: QWidget) -> list[QLabel | str]:
    plain_text = ''
    emojis: list[QLabel] = []
    has_words = False
    final: list[QLabel | str] = []
    for match in cls.grapheme_splitter.finditer(content):
      grapheme = content[slice(*match.span())]
      if grapheme in cls.emoji_mapping:
        if plain_text:
          final.append(plain_text)
          if not has_words:
            has_words = bool(plain_text.split())
          plain_text = ''
        emoji = QLabel(parent)
        path = 'emojis/' + cls.emoji_mapping[grapheme][0]
        emoji.style('image', f'url("{root.absoluteFilePath(path)}")')
        emojis.append(emoji)
        final.append(emoji)
      else:
        plain_text += grapheme
    if plain_text:
      final.append(plain_text)
    jumboable = not has_words and len(emojis) <= 30
    emoji_size = QSize(48, 48) if jumboable else QSize(22, 22)
    for emoji in emojis: emoji.setFixedSize(emoji_size)
    return final

class ImageRenderer(RoundedIconMixin, QPushButton):
  
  folder = QDir(root.absoluteFilePath('attachments'))
  makedirs(folder.absolutePath(), exist_ok=True)

  network_manager = QNetworkAccessManager()
  image_loaded = pyqtSignal(object)

  @classmethod
  def hash(cls, message: str) -> int:
    hash = 0
    for char in message:
      hash = (hash * 281 ^ ord(char) * 997) & 0xffffffffffffffff
    return hash
  
  def __init__(
    self, parent: QWidget, source: DAttachment | DEmbedProxy
  ) -> None:
    super().__init__(parent)

    self.original: QPixmap | None = None
    self.setSizePolicy(QSP.Policy.Expanding, QSP.Policy.Preferred)
    
    if isinstance(source, DAttachment):
      file_name = f'{source.id}.{source.content_type[6:]}'
      downloader = self.download_attachment
    elif isinstance(source, DEmbedProxy):
      ext = source.proxy_url.split('.')[-1]
      file_name = f'{abs(self.hash(source.url))}.{ext}'
      downloader = self.download_media_proxy
    else: raise ValueError(f'invalid image source: {source}')
    self.file_path = self.folder.absoluteFilePath(file_name)

    self.height_for_width = source.height / source.width
    width_ratio = self.maximumWidth() / source.width
    height_ratio = self.maximumHeight() / source.height
    ratio = min(width_ratio, height_ratio, 1.)
    self.setMaximumWidth(int(source.width * ratio))
    self.setMaximumHeight(int(source.height * ratio))

    if self.folder.exists(file_name):
      self.load_image()
    else:
      downloader(source)
  
  def hasHeightForWidth(self) -> bool: return True
  def heightForWidth(self, width: int) -> int:
    return int(self.height_for_width * width)

  def resizeEvent(self, _) -> None:
    if self.original: self.set_brush()

  def download_attachment(self, attachment: DAttachment) -> None:
    self.image_loaded.connect(self.load_image)
    future = client.submit(attachment.save(self.file_path))
    future.add_done_callback(self.image_loaded.emit)

  def download_media_proxy(self, media_proxy: DEmbedProxy) -> None:
    request = QNetworkRequest(QUrl(media_proxy.proxy_url))
    self.reply = self.network_manager.get(request)
    self.reply.finished.connect(self.load_image)

  def load_image(self, future: Future[int] | None=None) -> None:
    # TODO handle exception from future or self.reply
    if hasattr(self, 'reply'):
      self.original = QPixmap.fromImageReader(QImageReader(self.reply))
      self.original.save(self.file_path)
    else:
      self.original = QPixmap(self.file_path)
    self.set_brush()

  def set_brush(self) -> None:
    self.brush = QBrush(self.original.scaled(
      self.size(), Qt.AspectRatioMode.KeepAspectRatio,
      Qt.TransformationMode.SmoothTransformation
    ))
    self.update()
