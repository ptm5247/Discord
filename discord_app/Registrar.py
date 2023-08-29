from concurrent.futures import Future
from os import makedirs
from typing import Callable

from discord_app import (
  QObject, DTextChannel, DGroupChannel, DDMChannel, DUser, DMember, DMessage,
  QTimerEvent, pyqtSignal, QBrush, QWidget, Qt, QImage, QDir, RRect, QLabel,
  QPainter, SmallTypingBubbles, QHBoxLayout, ElidedQLabel, QVBoxLayout,
  QPushButton,
  DAbstractUser, DGuild, DAsset, DStatus, DMessageableChannel, DGame,
  DStreaming, DCustomActivity, DActivity, DActivityType,
  dsignals, qsignals, client, root, state, _log, State
)

class Registrar:

  def __init__(self) -> None:
    self.typing = TypingRegistry()
    dsignals.on_typing.connect(self.typing.on_typing)
    dsignals.on_message.connect(self.typing.on_message)
    dsignals.on_guild_update.connect(self.on_guild_update)
    dsignals.on_member_update.connect(self.on_user_update)
    dsignals.on_presence_update.connect(self.on_presence_update)
    dsignals.on_user_update.connect(self.on_user_update)
  
  def typing_users(self) -> list[str]:
    if state.selected_channel:
      return list(self.typing.typing_by_id[state.selected_channel.id])
    else: return []
    
  def is_typing(self, user: DAbstractUser) -> bool:
    if state.selected_channel:
      name = self.typing.get_name_of(user)
      return name in self.typing.typing_by_id[state.selected_channel.id]
    else: return False

  def on_guild_update(self, before: DGuild, after: DGuild) -> None:
    if before.icon != after.icon:
      AssetBrush.update_asset(after)
  
  def on_user_update(self, before: DAbstractUser, after: DAbstractUser) -> None:
    if before.display_name != after.display_name:
      Username.user_update(after)
    if before.display_avatar != after.display_avatar:
      AssetBrush.update_asset(after)
  
  def on_presence_update(self, before: DMember, after: DMember) -> None:
    if before.activity != after.activity:
      Activity.member_update(after)
    if before.status != after.status:
      Avatar.user_update(after)
  
  def AssetBrush(
    self, parent: QWidget, source: DAbstractUser | DGuild=None
  ) -> 'AssetBrush':
    brush = AssetBrush(parent)
    if source: brush.set_asset(source, parent.width())
    return brush
  
  def Avatar(
    self, parent: QWidget, tooltip: bool, typing: bool, offline: bool,
    source: DAbstractUser=None
  ) -> 'Avatar':
    avatar = Avatar(parent, tooltip, typing, offline)
    if source: avatar.set_asset(source)
    return avatar
  
  def Username(
    self, parent: QWidget, source: DUser | DMember,
    context: DMessageableChannel, show_owner: bool, show_bot: bool
  ) -> 'Username':
    return Username(parent, source, context, show_owner, show_bot)
  
  def Activity(self, parent, source: DUser | DMember) -> 'Activity':
    if isinstance(source, DUser):
      guilds = source.mutual_guilds
      source = guilds[0].get_member(source.id) if guilds else None
    return Activity(parent, source)
  
  def User(
    self, parent: QWidget, user: DUser | DMember, context: DMessageableChannel,
    active=False, typing=True, show_tags=True, offline=False
  ) -> 'User':
    return User(
      self, parent, user, context, active, typing, show_tags, offline
    )

class Observable(QObject):
  updated = pyqtSignal(str)

class TypingRegistry(QObject):

  def __init__(self) -> None:
    self.typing_by_id: dict[int, dict[str, int]] = {}
    self.typing_by_timer: dict[int, tuple[int, str]] = {}

  @staticmethod
  def get_name_of(user: DUser | DMember) -> str:
    return '' if user.id == client.user.id else user.display_name
  
  def was_typing(self, timer_by_name: dict[str, int], name: str) -> bool:
    if timer := timer_by_name.get(name, 0):
      self.killTimer(timer)
      self.typing_by_timer.pop(timer)
    return bool(timer)

  def on_typing(
    self, channel: DTextChannel | DGroupChannel | DDMChannel,
    user: DUser | DMember
  ) -> None:
    timer_by_name = self.typing_by_id.setdefault(channel.id, {})
    name = self.get_name_of(user)
    update = not self.was_typing(timer_by_name, name)
    timer_by_name[name] = (timer := self.startTimer(10000))
    self.typing_by_timer[timer] = (channel.id, name)
    if update: qsignals.typing_registry_update.emit()
  
  def on_message(self, message: DMessage) -> None:
    if timer_by_name := self.typing_by_id.get(message.channel.id, {}):
      name = self.get_name_of(message.author)
      if self.was_typing(timer_by_name, name):
        qsignals.typing_registry_update.emit()
  
  def timerEvent(self, event: QTimerEvent) -> None:
    self.killTimer(timer := event.timerId())
    if timer in self.typing_by_timer:
      channel_id, name = self.typing_by_timer.pop(timer)
      self.typing_by_id[channel_id].pop(name)
    qsignals.typing_registry_update.emit()

class AssetBrush(QBrush):

  registry: dict[int, dict[int, Observable]] = {}
  pending: dict[str, Future] = {}

  def __init__(self, parent: QWidget) -> None:
    super().__init__(Qt.GlobalColor.transparent)
    self.parent = parent

  def update_parent(self, texture_path: str | None) -> None:
    if texture_path:
      self.setTextureImage(QImage(texture_path))
    else:
      self.setStyle(Qt.BrushStyle.SolidPattern)
    self.parent.update()

  # not automatic since QBrush is not a QObject
  def disconnect(self) -> None:
    QObject.disconnect(self.connection)

  @staticmethod
  def get_dir_for(source: DAbstractUser | DGuild) -> tuple[DAsset, QDir]:
    if isinstance(source, DAbstractUser):
      asset, folder = source.display_avatar, 'avatars'
    elif isinstance(source, DGuild):
      asset, folder = source.icon, 'icons'
    else: raise ValueError(f'invalid asset source {source}')
    dir = QDir(root.absoluteFilePath(f'cache/{folder}/{source.id}'))
    makedirs(dir.absolutePath(), exist_ok=True)
    return asset, dir

  def set_asset(self, source: DAbstractUser | DGuild, size: int) -> None:
    asset, dir = self.get_dir_for(source)
    if asset: self.save(asset, size, dir, self.update_parent)
    else:     self.update_parent('')
    self.connection = self.registry.setdefault(source.id, {}) \
      .setdefault(size, Observable()).updated.connect(self.update_parent)
    self.parent.destroyed.connect(self.disconnect)

  @classmethod
  def save(
    cls, original: DAsset, size: int, dir: QDir, callback: Callable[[str], None]
  ) -> None:
    asset = original.replace(size=size, static_format='png')
    file_name = f'{asset.key}.{size}.png'
    file_path = dir.absoluteFilePath(file_name)
    if asset.is_animated(): _log.warn(f'{file_path} is animated...')

    if dir.exists(file_name):
      callback(file_path)
    elif future := cls.pending.get(file_path):
      cls.update_later(file_path, future, callback)
    else:
      future = client.submit(asset.save(file_path))
      cls.pending[file_path] = future
      cls.update_later(file_path, future, callback)

  @classmethod
  def update_later(
    cls, file_path: str, future: Future[int], callback: Callable[[str], None]
  ) -> None:
    def _callback(_: int):
      cls.pending.pop(file_path, None)
      callback(file_path)
    future.add_done_callback(_callback)
  
  @classmethod
  def update_asset(cls, source: DAbstractUser | DGuild) -> None:
    if observable_by_size := cls.registry.get(source.id, {}):
      asset, dir = cls.get_dir_for(source)
      for size, observable in observable_by_size.items():
        cls.save(asset, size, dir, observable.updated.emit)

class Avatar(QWidget):

  registry: dict[int, Observable] = {}

  base_mask = RRect(0, 0, 32, 32, 16, 16)
  round_mask = base_mask - RRect(19, 19, 16, 16, 8, 8)
  mobile_mask = base_mask - RRect(19, 14, 16, 21, 4.2, 4.2)
  typing_mask = base_mask - RRect(11.5, 19, 31, 16, 8, 8)

  # TODO
  # online_mobile_path = RRect((0)*W, (0)*H, W, H, .1875*W, .125*H) \
  #   - RRect((.125)*W, (.166666666667)*H, .75*W, .5*H) \
  #   - RRect((.375)*W, (.75)*H, .25*W, .166666666667*H, .125*W, .083333333333*H)
  online_path = RRect(22, 22, 10, 10, 5, 5)
  idle_path = online_path - RRect(20.75, 20.75, 7.5, 7.5, 3.75, 3.75)
  dnd_path = online_path - RRect(23.25, 25.75, 7.5, 2.5, 1.25, 1.25)
  offline_path = online_path - RRect(24.5, 24.5, 5, 5, 2.5, 2.5)
  typing_path = RRect(14.5, 22, 25, 10, 5, 5)

  online_color = 0x23a55a
  idle_color = 0xf0b232
  dnd_color = 0xf23f43
  offline_color = 0x80848e

  def __init__(
    self, parent: QWidget, tooltip: bool, typing: bool, offline: bool
  ) -> None:
    super().__init__(parent)

    self.brush = AssetBrush(self)
    self.status_path: RRect = None
    self.status_color: int = None
    self.source: DAbstractUser | None = None
    self.typing = False

    self.show_tooltip = tooltip
    if tooltip:
      self.tooltip = QLabel(self, name='StatusZone')

    self.show_typing = typing
    if typing:
      qsignals.typing_registry_update.connect(self.typing_registry_update)
      self.bubbles = SmallTypingBubbles(self)

    self.show_offline = offline

  def disconnect(self) -> None:
    QObject.disconnect(self.connection)

  def set_vars(
    self, status_path: RRect, status_color: int, tooltip: str | None=None
  ) -> None:
    self.status_path = status_path
    self.status_color = status_color
    if self.show_tooltip:
      if tooltip: self.tooltip.style('tooltip', tooltip, State.HOVER)
      else:       self.tooltip.style('tooltip', None)

  def set_asset(self, source: DAbstractUser) -> None:
    self.brush.set_asset(source, 32)
    self.source = source

    observable = self.registry.setdefault(source.id, Observable())
    self.connection = observable.updated.connect(self.updated)
    self.destroyed.connect(self.disconnect)

  def updated(self) -> None:
    is_self = self.source and self.source.id == client.user.id
    guilds: list[DGuild] = self.source.mutual_guilds
    match guilds[0].get_member(self.source.id).status if guilds else None:
      case DStatus.online:
        self.set_vars(self.online_path, self.online_color, 'Online')
      case DStatus.idle:
        self.set_vars(self.idle_path, self.idle_color, 'Idle')
      case DStatus.dnd:
        self.set_vars(self.dnd_path, self.dnd_color, 'Do Not Disturb')
      case DStatus.offline if is_self or self.show_offline:
        tooltip = 'Invisible' if is_self else 'Offline'
        self.set_vars(self.offline_path, self.offline_color, tooltip)
      case _: self.set_vars(None, None)
    self.update()
  
  def typing_registry_update(self) -> None:
    if self.source:
      should_be_typing = registrar.is_typing(self.source)
      if should_be_typing != self.typing:
        self.typing = should_be_typing
        self.update()

  def paintEvent(self, _) -> None:
    painter = QPainter(self)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    if self.status_path:
      if self.typing:
        painter.fillPath(self.typing_mask, self.brush)
        painter.fillPath(self.typing_path, self.status_color)
        self.bubbles.show()
      else:
        painter.fillPath(self.round_mask, self.brush)
        painter.fillPath(self.status_path, self.status_color)
        if self.show_typing: self.bubbles.hide()
    else:
      painter.fillPath(self.base_mask, self.brush)
      if self.show_typing: self.bubbles.hide()

  @classmethod
  def user_update(cls, source: DUser | DMember) -> None:
    if observable := cls.registry.get(source.id, None):
      observable.updated.emit('')

class Username(QWidget):

  registry: dict[int, Observable] = {}

  def __init__(
    self, parent: QWidget, source: DUser | DMember,
    context: DMessageableChannel, show_owner: bool, show_bot: bool
  ) -> None:
    super().__init__(parent, layout=QHBoxLayout)

    self.source = source
    self.use_global = isinstance(source, DUser)
    self.text = QLabel(self, name='Username')
    self.updated()

    self.layout().addWidget(self.text)
    owner = (hasattr(context, 'owner') and context.owner == source) or \
            (hasattr(context, 'guild') and context.guild.owner == source)
    if show_owner and owner:
      self.layout().addSpacing(4)
      self.layout().addWidget(QLabel(self, name='ServerOwner'))
    if show_bot and source.bot:
      tag = QWidget(self, layout=QHBoxLayout, name='BotTag')
      if source.public_flags.verified_bot:
        tag.layout().addSpacing(-4)
        tag.layout().addWidget(QLabel(tag, name='Verified'))
      tag.layout().addWidget(QLabel('BOT', tag))
      self.layout().addWidget(tag)
    if self.layout().count() > 1:
      self.layout().addStretch(1)
    
    observable = self.registry.setdefault(source.id, Observable())
    self.connection = observable.updated.connect(self.updated)
    self.destroyed.connect(self.disconnect)

  def disconnect(self) -> None:
    QObject.disconnect(self.connection)
    
  def updated(self) -> None:
    if self.use_global:
      self.text.setText(self.source.global_name or self.source.name)
    else:
      self.text.setText(self.source.display_name)
      color = str(self.source.color) if self.source.color.value else None
      self.text.style('color', color)

  @classmethod
  def user_update(cls, source: DUser | DMember) -> None:
    if observable := cls.registry.get(source.id, None):
      observable.updated.emit('')

class Activity(QWidget):

  registry: dict[int, Observable] = {}

  def __init__(self, parent: QWidget, source: DMember | None) -> None:
    super().__init__(parent, layout=QHBoxLayout)

    self.source = source
    self.text = ElidedQLabel(self)
    self.bold = ElidedQLabel(self, name='Bold')

    self.layout().addWidget(self.text)
    self.layout().addWidget(self.bold)
    self.layout().addStretch(1)

    id = source.id if source else 0
    observable = self.registry.setdefault(id, Observable())
    self.connection = observable.updated.connect(self.updated)
    self.destroyed.connect(self.disconnect)

  def disconnect(self) -> None:
    QObject.disconnect(self.connection)

  def updated(self) -> None:
    match activity := self.source.activity if self.source else None:
      case None:
        self.set_text(None)
      case DActivity(type=DActivityType.playing, name=n) | DGame(name=n):
        self.set_text('Playing ', n)
      case DActivity(type=DActivityType.streaming, name=n) | DStreaming(name=n):
        self.set_text('Streaming ', n)
      case DActivity(type=DActivityType.listening, name=n):
        self.set_text('Listening to ', n)
      case DActivity(type=DActivityType.watching, name=n):
        self.set_text('Watching ', n)
      case DCustomActivity() | _:
        self.set_text(str(activity))
  
  def set_text(self, normal: str, bold: str=None) -> None:
    if normal:
      self.text.setText(normal)
      self.bold.setText(bold)
      self.bold.show() if bold else self.bold.hide()
      self.show()
    else:
      self.hide()

  @classmethod
  def member_update(cls, source: DMember) -> None:
    if observable := cls.registry.get(source.id, None):
      observable.updated.emit('')

class User(QPushButton):

  active = pyqtSignal(bool)

  def __init__(
    self, parent: QWidget, user: DUser | DMember, context: DMessageableChannel,
    active=False, typing=True, show_tags=True, offline=False
  )-> None:
    super().__init__(parent, layout=QHBoxLayout)
    self.setObjectName(hex(user.id))
    self.active.emit(active)

    self.avatar = registrar.Avatar(self, True, typing, offline, user)
    self.name = registrar.Username(self, user, context, show_tags, show_tags)
    self.activity = registrar.Activity(self, user)

    self.layout().addWidget(self.avatar)
    container = QWidget(self, layout=QVBoxLayout)
    self.layout().addWidget(container)
    container.layout().addStretch(1)
    container.layout().addWidget(self.name)
    container.layout().addSpacing(-2)
    container.layout().addWidget(self.activity)
    container.layout().addStretch(1)

registrar = Registrar()

__all__ = ['registrar']
