import regex

from discord_app import (
  DGuild,
  pyqtSignal, Qt, QMargins, QMimeData, QPoint, QMouseEvent, QDrag,
  QDragEnterEvent, QDragMoveEvent, QDropEvent, QPixmap, QPainter, QSvgWidget,
  QWidget, QPushButton, QGridLayout, QLabel, QButtonGroup,
  discord, state, dsignals, qsignals, registrar,
  State, RoundedIconMixin, ScrollArea
)

import discord_app._utils as utils

class GuildList(ScrollArea):
  
  def __init__(self, parent: QWidget) -> None:
    super().__init__(parent)
    self.setAcceptDrops(True)

    self.button_group = QButtonGroup(self)
    self.divider = QWidget(self, name='GuildListDivider')
    self.insert = GuildListInsert(self)

    self.add_widget(Guild(self, None))
    self._layout().addWidget(self.divider)

    dsignals.on_guild_join.connect(self.guild_join)
    # dsignals.on_guild_name_update.connect(self.guild_name_update)
    dsignals.on_guild_remove.connect(self.guild_remove)
  
  def add_widget(self, guild: 'Guild') -> None:
    self._layout().addWidget(guild)
    self.button_group.addButton(guild.icon)

  def get_widget(self, guild: DGuild) -> 'Guild':
    return self._content.findChild(
      Guild, hex(guild.id), Qt.FindChildOption.FindDirectChildrenOnly
    )

  def dragEnterEvent(self, event: QDragEnterEvent) -> None:
    event.accept()

  def dragMoveEvent(self, event: QDragMoveEvent) -> None:
    self._dragMoveEvent(self.mapToGlobal(event.position()).toPoint())
  
  def _dragMoveEvent(self, global_position: QPoint) -> None:
    layout = self._layout()
    first = layout.itemAt(layout.indexOf(self.divider) + 1).widget()
    last = layout.itemAt(layout.count() - 1).widget()
    local_position = self._content.mapFromGlobal(global_position)

    if local_position.y() < first.pos().y():
      widget, above = first, True
    elif widget := self._content.childAt(local_position):
      while not isinstance(widget, Guild):
        widget = widget.parentWidget()
      local_position = widget.mapFromGlobal(global_position)
      above = local_position.y() < widget.contentsRect().center().y()
    else:
      widget, above = last, False
    
    self.insert.show_here(widget, above)
  
  def dropEvent(self, event: QDropEvent) -> None:
    layout = self._layout()
    source_idx = layout.indexOf(event.source().parentWidget())
    dest_idx = layout.indexOf(self.insert.guild) + 1 - self.insert.above
    dest_idx -= dest_idx > source_idx
    if source_idx != dest_idx:
      layout.insertWidget(dest_idx, layout.takeAt(source_idx).widget())
    self.insert.hide()

    order = range(layout.indexOf(self.divider) + 1, layout.count())
    order = list(map(lambda i: layout.itemAt(i).widget().guild.id, order))
    state.guild_ordering = order
  
  def dragLeaveEvent(self, _) -> None:
    self.insert.hide()

  def fill(self) -> None:
    ids = [guild.id for guild in discord.api.guilds]
    state.guild_ordering = \
      [id for id in state.guild_ordering if id in ids] + \
      [id for id in ids if id not in state.guild_ordering]
    for guild in map(discord.api.get_guild, state.guild_ordering):
      self.add_widget(widget := Guild(self, guild))
      if guild.id == state.last_guild_id:
        widget.icon.toggle()
    if not self.button_group.checkedButton():
      self._layout().itemAt(0).widget().icon.toggle()
  
  def guild_join(self, guild: DGuild) -> None:
    self.add_widget(Guild(self, guild))
  
  def guild_name_update(self, guild: DGuild) -> None:
    self.get_widget(guild).icon.set_name()

  def guild_remove(self, guild: DGuild) -> None:
    self.get_widget(guild).deleteLater()
  
class Guild(QWidget):

  notify = pyqtSignal(bool)

  def __init__(self, parent: GuildList, guild: DGuild | None) -> None:
    super().__init__(parent, layout=QGridLayout)
    self.setObjectName(hex(guild.id if guild else 0))

    self.guild = guild
    self.default_margins = self.layout().contentsMargins()
    self.pressed_margins = self.default_margins + QMargins(0, 1, 0, -1)

    self.icon = Icon(self, parent)
    QLabel(self, name='Pill')
    if self.has_unread_messages(): self.notify.emit(True)

    self.layout().addWidget(self.icon)
    self.icon.pressed.connect(self.handle_icon_pressed)
    self.icon.released.connect(self.handle_icon_released)

  def has_unread_messages(self) -> bool:
    return any(map(utils.has_unread_messages,
      self.guild.text_channels + self.guild.voice_channels
    )) if self.guild else False

  def handle_icon_pressed(self) -> None:
    self.layout().setContentsMargins(self.pressed_margins)
  
  def handle_icon_released(self) -> None:
    self.layout().setContentsMargins(self.default_margins)

class Icon(RoundedIconMixin, QPushButton):

  dragged = pyqtSignal(bool)

  GUILD_NAME_ABBREVIATOR = regex.compile(r'(\w)\S*\b|([\(\)\[\]\{\}])+')

  def __init__(self, parent: Guild, list: GuildList) -> None:
    super().__init__(parent, layout=QGridLayout)
    self.setCheckable(True)
    self.setAcceptDrops(True)

    self.guild = parent.guild
    self.list = list
    self.brush = registrar.AssetBrush(self)
    self.set_name()

    if not self.guild:
      self.layout().addWidget(QSvgWidget('local:discord.svg', self))
    elif self.guild.icon:
      self.brush.set_asset(self.guild, self.width())

    self.toggled.connect(self.handle_toggled)
  
  def set_name(self) -> None:
    if self.guild:
      name = self.guild.name
      matches = self.GUILD_NAME_ABBREVIATOR.findall(name)
      self.setText(''.join(char for match in matches for char in match))
    else:
      name = 'Direct Messages'
    self.style('tooltip', name, State.DRAGHOVER | State.UNDRAGGED)
    self.style('tooltip', name, State.HOVER)

  def dragEnterEvent(self, event: QDragEnterEvent) -> None:
    event.accept()

  def dragMoveEvent(self, event: QDragMoveEvent) -> None:
    self.list._dragMoveEvent(self.mapToGlobal(event.position()).toPoint())
  
  def dropEvent(self, event: QDropEvent) -> None:
    self.list.dropEvent(event)

  def handle_toggled(self, checked: bool) -> None:
    if checked:
      qsignals.guild_selected.emit(self.guild)

  def mouseMoveEvent(self, event: QMouseEvent) -> None:
    if Qt.MouseButton.LeftButton in event.buttons() and self.guild:
      pixmap = QPixmap(self.size())
      pixmap.fill(Qt.GlobalColor.transparent)
      painter = QPainter(pixmap)
      painter.setOpacity(.75)
      self.render(painter, flags=self.RenderFlag.DrawChildren)
      painter.end()

      self.released.emit()
      self.dragged.emit(True)
      text = self.text()
      self.setText('')
      
      drag = QDrag(self)
      drag.setMimeData(QMimeData())
      drag.setPixmap(pixmap)
      drag.setHotSpot(event.pos())
      drag.exec()

      self.setText(text)
      self.dragged.emit(False)

class GuildListInsert(QWidget):
  '''The small divider that appears between guilds when rearranging'''

  def __init__(self, parent: GuildList) -> None:
    super().__init__(parent)
    self.content_transform = parent.content_transform
    self.hide()

  def show_here(self, by: Guild, above: bool=True) -> None:
    self.guild, self.above = by, above
    position = self.content_transform().map(by.geometry().topLeft())
    gap = (by.height() - by.layout().contentsRect().height() - self.height())
    position += QPoint(0, (not above) * by.height() - self.height() - gap // 2)
    self.move(position)
    self.show()
