from discord_app import (
  DRole, DMember, DGuild, DTextChannel, DMessageable,
  Qt, QGridLayout, QLabel, QVBoxLayout, QWidget,
  dsignals, qsignals, registrar, ScrollArea
)

from typing import TYPE_CHECKING
if TYPE_CHECKING:
  from discord_app.Registrar import User

from discord.utils import get

class MemberList(ScrollArea):
  
  def __init__(self, parent: QWidget) -> None:
    super().__init__(parent)
    self._layout().setDirection(QVBoxLayout.Direction.BottomToTop)
    self.guild: DGuild | None = None
    qsignals.channel_selected.connect(self.channel_selected)
    dsignals.on_guild_role_create.connect(self.guild_role_create)
    dsignals.on_guild_role_delete.connect(self.guild_role_delete)
    # dsignals.on_guild_role_hoist_update.connect(self.guild_role_hoist_update)
    # dsignals.on_guild_role_name_update.connect(self.guild_role_name_update)
    # dsignals.on_guild_role_position_update.connect(self.guild_role_position_update)
    # dsignals.on_member_activity_update.connect(self.member_activity_update)
    dsignals.on_member_join.connect(self.member_join)
    # dsignals.on_member_online_update.connect(self.member_roles_update)
    dsignals.on_member_remove.connect(self.member_remove)
    # dsignals.on_member_roles_update.connect(self.member_roles_update)
    # dsignals.on_member_status_update.connect(self.member_status_update)
  
  def get_member(self, member: DMember | None) -> 'User':
    return self._content.findChild(User, hex(member.id))

  def get_role(self, role: DRole | None) -> 'Role':
    return self._content.findChild(
      Role, hex(role.id if role else 0),
      Qt.FindChildOption.FindDirectChildrenOnly
    )
  
  def get_role_for(self, member: DMember) -> 'Role':
    if member.raw_status == 'offline':
      return self._layout().itemAt(0).widget()
    else:
      top = get(reversed(member.roles), hoist=True) or member.guild.default_role
      return self.get_role(top)

  def channel_selected(self, channel: DMessageable | None) -> None:
    for role in self._content.findChildren(
      Role, options=Qt.FindChildOption.FindDirectChildrenOnly
    ): role.clear()
    if isinstance(channel, DTextChannel):
      if channel.guild is not self.guild:
        self.clear()
        self.guild = channel.guild
        self._layout().addWidget(Role(self, None))
        for role in channel.guild.roles:
          if role.hoist or role.is_default():
            self._layout().addWidget(Role(self, role))
      for member in channel.members:
        self.member_join(member)
  
  def guild_role_create(self, role: DRole) -> None:
    i = [r for r in role.guild.roles if r.hoist].index(role) + 2
    self._layout().insertWidget(i, Role(self, role))
    self.guild_role_position_update(role)
  
  def guild_role_delete(self, role: DRole) -> None:
    old_role_widget = self.get_role(role)
    for member_widget in old_role_widget.findChildren(User):
      self.member_roles_update(member_widget.member, member_widget)
    old_role_widget.deleteLater()
  
  def guild_role_hoist_update(self, role: DRole) -> None:
    if role.hoist: self.guild_role_create(role)
    else:          self.guild_role_delete(role)
  
  def guild_role_name_update(self, role: DRole) -> None:
    self.get_role(role).header.set_name()
  
  def guild_role_position_update(self, role: DRole) -> None:
    # TODO rearrange in layout
    role_widget = self.get_role(role)
    for member in role.members:
      if self.get_role_for(member) is role_widget:
        if member_widget := self.get_member(member):
          role_widget.add_member(member_widget)

  def member_activity_update(self, member: DMember) -> None:
    if widget := self.get_member(member): widget.set_activity()
  
  def member_join(self, member: DMember) -> None:
    widget = registrar.User(role := self.get_role_for(member), member)
    role.add_member(widget, force_add=True)
  
  def member_remove(self, member: DMember) -> None:
    if widget := self.get_member(member): widget.deleteLater()

  def member_roles_update(self, member: DMember, widget: 'User'=None) -> None:
    if widget := (widget or self.get_member(member)):
      self.get_role_for(member).add_member(widget)

  def member_status_update(self, member: DMember) -> None:
    if widget := self.get_member(member):  widget.set_status()
  
class Role(QWidget):

  def __init__(self, parent: MemberList, role: DRole | None) -> None:
    super().__init__(parent, layout=RoleLayout)
    self.setObjectName(hex(role.id if role else 0))

    self.header = RoleHeader(self, role)

    self.layout().addWidget(self.header)
    self.hide()
  
  def clear(self) -> None:
    while member_item := self.layout().takeAt(1):
      member_item.widget().deleteLater()
    self.header.set_name()

  def add_member(self, member: 'User', force_add=False) -> None:
    if member.parentWidget() is not self or force_add:
      self.layout().addWidget(member)
      member.active.emit(member.member.raw_status != 'offline')

class RoleLayout(QVBoxLayout):

  def addWidget(self, widget: QWidget, *args) -> None:
    if widget.parentWidget() is not self.parentWidget():
      widget.parentWidget().layout().removeWidget(widget)
    super().addWidget(widget, *args)
    self.parentWidget().header.set_name()

  def removeWidget(self, *args) -> None:
    super().removeWidget(*args)
    self.parentWidget().header.set_name()

class RoleHeader(QWidget):

  def __init__(self, parent: Role, role: DRole | None):
    super().__init__(parent, layout=QGridLayout)

    self.role = role
    self.label = QLabel(self)

    self.layout().addWidget(self.label)

  def set_name(self) -> None:
    name = 'OFFLINE' if self.role is None else \
           'ONLINE' if self.role.is_default() else \
           self.role.name.upper()
    if count := self.parentWidget().layout().count() - 1:
      self.label.setText(f'{name} — {count}')
      self.parentWidget().show()
    else:
      self.parentWidget().hide()
