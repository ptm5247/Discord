from typing import Callable

from discord_app import (
  DGuild, DCategoryChannel, DTextChannel, DVoiceChannel, DGuildChannel,
  _log,
  Qt, pyqtSignal, QWidget, QHBoxLayout, QLabel, QPushButton, QVBoxLayout,
  QButtonGroup, QStackedLayout, QGridLayout,
  registrar, state, qsignals, dsignals, client,
  State, ChannelDropdown, MultiShadow, ScrollArea
)

from typing import TYPE_CHECKING
if TYPE_CHECKING:
  from discord_app.Registrar import User

DCategory = DCategoryChannel | None
DChannel = DTextChannel | DVoiceChannel
from discord.utils import get

import discord_app._utils as utils

class NavigationPane(QWidget):

  def __init__(self, parent: QWidget) -> None:
    super().__init__(parent, layout=QStackedLayout)

    self.guild_header = GuildHeader(self)
    self.guild_header.setGraphicsEffect(MultiShadow())
    self.channel_list = ChannelList(self)
    self.search_header = SearchHeader(self)
    self.search_header.setGraphicsEffect(MultiShadow())
    self.dm_list = DMList(self)

    guild_widget = QWidget(self, layout=QVBoxLayout)
    dm_widget = QWidget(self, layout=QVBoxLayout)

    guild_widget.layout().addWidget(self.guild_header)
    guild_widget.layout().addWidget(self.channel_list)
    self.layout().addWidget(guild_widget)
    dm_widget.layout().addWidget(self.search_header)
    dm_widget.layout().addWidget(self.dm_list)
    self.layout().addWidget(dm_widget)

    qsignals.guild_selected.connect(self.guild_selected)
    # dsignals.on_guild_name_update.connect(self.guild_name_update)

  def guild_selected(self, guild: DGuild | None) -> None:
    self.channel_list.clear()
    self.dm_list.clear()
    if guild:
      self.layout().setCurrentIndex(0)
      self.guild_header.raise_()
      self.guild_name_update(guild)
      self.channel_list.guild_selected(guild)
    else:
      self.layout().setCurrentIndex(1)
      self.search_header.raise_()
      self.dm_list.guild_selected(guild)
  
  def guild_name_update(self, guild: DGuild) -> None:
    if guild == state.selected_guild:
      self.guild_header.label.setText(guild.name)

class SearchHeader(QWidget):

  def __init__(self, parent: NavigationPane) -> None:
    super().__init__(parent, layout=QGridLayout)
    self.search = QLabel('Find or start a conversation', self)
    self.layout().addWidget(self.search)

class DMList(ScrollArea):

  def __init__(self, parent: NavigationPane) -> None:
    super().__init__(parent)
    self.clear()
    qsignals.dm_registry_update.connect(self.dm_registry_update)

  def clear(self, soft=False) -> None:
    self.dm_group = QButtonGroup(self)
    if not soft: super().clear()

  def guild_selected(self, _: None) -> None:
    self._layout().addWidget(CategoryHeader(self))
    self.fill()

  def fill(self) -> None:
    members = client.get_all_members()
    mapping = { member.member.id: member
      for member in self._content.findChildren(
        User, options=Qt.FindChildOption.FindDirectChildrenOnly
    )}
    for i, member_id in enumerate(state.dm_list):
      if not (widget := mapping.get(member_id, None)):
        member = get(members, id=member_id)
        widget = registrar.User(self, member, active=True, show_typing=False,
                 show_tags=False, show_offline=True, use_global=True)
        widget.setCheckable(True)
        widget.toggled.connect(self.get_channel_selector(widget))
        self.dm_group.addButton(widget)
      self._layout().insertWidget(i + 1, widget)

  # TODO move into Member, get rid of excessive flags if only 2 use cases
  @staticmethod
  def get_channel_selector(member: 'User') -> Callable[[bool], None]:
    def toggle(checked: bool) -> None:
      if checked:
        if member.member.id in state.dm_history:
          channel = state.dm_history[member.member.id][0].channel
          qsignals.channel_selected.emit(channel)
        else:
          qsignals.dm_registry_update.connect(
            lambda: toggle(checked), Qt.ConnectionType.SingleShotConnection
          )
    return toggle
  
  def dm_registry_update(self) -> None:
    if state.selected_guild is None:
      self.clear(soft=True)
      self.fill()
  
class GuildHeader(QWidget):

  def __init__(self, parent: NavigationPane) -> None:
    super().__init__(parent, layout=QGridLayout)
    self.label = QLabel(self)
    self.layout().addWidget(self.label)
  
class ChannelList(ScrollArea):
  
  def __init__(self, parent: NavigationPane) -> None:
    super().__init__(parent)
    self.clear()

    dsignals.on_guild_channel_create.connect(self.guild_channel_create)
    dsignals.on_guild_channel_delete.connect(self.guild_channel_delete)
    # dsignals.on_guild_channel_icon_update.connect(self.guild_channel_icon_update)
    # dsignals.on_guild_channel_name_update.connect(self.guild_channel_name_update)
    # dsignals.on_guild_channel_position_update.connect(
    #   self.guild_channel_position_update
    # )

  def clear(self) -> None:
    self.text_group = QButtonGroup(self)
    self.voice_group = QButtonGroup(self)
    return super().clear()

  def add_widget(self, category: 'Category') -> None:
    categories, _ = zip(*state.selected_guild.by_category())
    i = categories.index(category.category)
    self._layout().insertWidget(i, category)
  
  def get_widget(self, channel: DGuildChannel | None) -> 'GuildChannel':
    if isinstance(channel, DCategory) or channel is None:
      return self._content.findChild(
        Category, hex(channel.id if channel else 0),
        Qt.FindChildOption.FindDirectChildrenOnly
      )
    else: return self._content.findChild(Channel, hex(channel.id))

  def get_button_group(self, channel: DChannel) -> QButtonGroup | None:
    match channel:
      case DTextChannel(): return self.text_group
      case DVoiceChannel(): return self.voice_group
      case _: return None

  def guild_selected(self, guild: DGuild) -> None:
    first_channel_widget: Channel = None # TODO lp might be voice
    last_channel_id = state.last_channel_id.get(guild.id, 0)
    for category, channels in guild.by_category():
      self.guild_channel_create(category)
      for channel in channels:
        channel_widget = self.guild_channel_create(channel)
        first_channel_widget = first_channel_widget or channel_widget
        if channel.id == last_channel_id:
          channel_widget.toggle()
    if not self.text_group.checkedButton() and \
      not self.voice_group.checkedButton():
      if first_channel_widget:
        first_channel_widget.toggle()
      else: qsignals.channel_selected.emit(None)

  def guild_channel_create(self, channel: DGuildChannel | None) -> \
    'GuildChannel':
    if isinstance(channel, DCategory) or channel is None:
      self.add_widget(widget := Category(self, channel))
    elif group := self.get_button_group(channel):
      group.addButton(widget := Channel(self, channel))
      category = self.get_widget(channel.category)
      category.insert_channel_widget(widget)
    else:
      _log.error(f'unsupported: create {channel.type} channel {channel}')
      widget = None
    return widget
  
  def guild_channel_delete(self, channel: DChannel) -> None:
    self.get_widget(channel).deleteLater()

  def guild_channel_icon_update(self, channel: DChannel) -> None:
    self.get_widget(channel).set_icon()

  def guild_channel_name_update(self, channel: DChannel) -> None:
    self.get_widget(channel).set_name()

  def guild_channel_position_update(self, channel: DChannel) -> None:
    for category, channels in (by_category := channel.guild.by_category()):
      if not (category_widget := self.get_widget(category)):
        category_widget = self.guild_channel_create(category, channel.guild)
      self.add_widget(category_widget)
      for channel in channels:
        channel_widget = self.get_widget(channel)
        category_widget.insert_channel_widget(channel_widget)
    while (count := self._layout().count()) > len(by_category):
      self._layout().takeAt(count - 1).widget().deleteLater()

class Category(QWidget):

  def __init__(self, parent: ChannelList, category: DCategory | None) -> None:
    super().__init__(parent, layout=QVBoxLayout)
    self.setObjectName(hex(category.id if category else 0))

    self.category = category
    self.collapsed = False
    self.header = CategoryHeader(self)
    self.set_name()

    self.layout().addWidget(self.header)
    
  def set_name(self) -> None:
    if self.category:
      self.header.label.setText(self.category.name.upper())

  def collapse(self, collapsed: bool) -> None:
    self.collapsed = collapsed
    op = Channel.hide_if_collapsed if collapsed else Channel.show
    for channel in self.findChildren(Channel):
      op(channel)
  
  def insert_channel_widget(self, channel: 'Channel') -> None:
    by_category = dict(state.selected_guild.by_category())
    i = by_category[channel.channel.category].index(channel.channel) + 1
    self.layout().insertWidget(i, channel)

    if self.collapsed:
      channel.hide()
    else:
      if self.category is None:
        self.show()
      channel.show()

class CategoryHeader(QWidget):

  def __init__(self, parent: Category | DMList) -> None:
    super().__init__(parent, layout=QVBoxLayout)

    if isinstance(parent, DMList):
      self.label = QPushButton(self)
      self.label.setText('DIRECT MESSAGES')
      self.layout().addWidget(self.label)
    elif parent.category:
      self.label = QPushButton(self)
      self.label.setCheckable(True)
      ChannelDropdown(self.label)
      self.layout().addWidget(self.label)
      self.label.toggled.connect(parent.collapse)
    else:
      self.style('height', '12px')

class Channel(QPushButton):

  notify = pyqtSignal(bool)

  def __init__(self, parent: Category, channel: DChannel) -> None:
    super().__init__(parent, layout=QHBoxLayout)
    self.setObjectName(hex(channel.id))
    self.setCheckable(True)

    self.channel = channel
    self.icon_ = QLabel(self, name='ChannelIcon')
    self.name = QLabel(self)
    QLabel(self, name='Pill')
    self.set_icon()
    self.set_name()
    if utils.has_unread_messages(channel): self.notify.emit(True)

    self.layout().addWidget(self.icon_)
    self.layout().addWidget(self.name)

    self.toggled.connect(self.handle_toggled)
  
  def set_icon(self) -> None:
    file_path, tooltip = utils.get_icon_type(self.channel)
    self.icon_.style('tooltip', tooltip, State.HOVER)
    self.icon_.style('image', file_path)

  def set_name(self) -> None:
    self.name.setText(self.channel.name)
  
  def handle_toggled(self, checked: bool) -> None:
    if checked: qsignals.channel_selected.emit(self.channel)
    else:       self.hide_if_collapsed()
    
  def hide_if_collapsed(self) -> None:
    if self.parentWidget().collapsed and not self.isChecked() and \
      not self.__style__.state & State.NOTIFY:
      self.hide()

GuildChannel = Category | Channel
