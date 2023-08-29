from dotenv     import load_dotenv
from os         import getenv
from os.path    import dirname
from sys        import argv
from threading  import current_thread
from typing     import Callable, Iterable, Protocol, TypeVar

from discord import (
  Activity            as DActivity,
  ActivityType        as DActivityType,
  Asset               as DAsset,
  Attachment          as DAttachment,
  AuditLogEntry       as DAuditLogEntry,
  AutoModAction       as DAutoModAction,
  AutoModRule         as DAutoModRule,
  CategoryChannel     as DCategoryChannel,
  Client              as DClient,
  CustomActivity      as DCustomActivity,
  DMChannel           as DDMChannel,
  Embed               as DEmbed,
  Emoji               as DEmoji,
  ForumChannel        as DForumChannel,
  Game                as DGame,
  GroupChannel        as DGroupChannel,
  Guild               as DGuild,
  GuildSticker        as DGuildSticker,
  Integration         as DIntegration,
  Intents             as DIntents,
  Interaction         as DInteraction,
  Invite              as DInvite,
  Member              as DMember,
  Message             as DMessage,
  PartialEmoji        as DPartialEmoji,
  PartialMessageable  as DPartialMessageable,
  TextChannel         as DTextChannel,
  Reaction            as DReaction,
  Role                as DRole,
  ScheduledEvent      as DScheduledEvent,
  StageChannel        as DStageChannel,
  StageInstance       as DStageInstance,
  Status              as DStatus,
  Streaming           as DStreaming,
  Thread              as DThread,
  ThreadMember        as DThreadMember,
  User                as DUser,
  VoiceChannel        as DVoiceChannel,
  VoiceState          as DVoiceState
)
from discord.abc import (
  GuildChannel        as DGuildChannel,
  Messageable         as DMessageable,
  PrivateChannel      as DPrivateChannel,
  User                as DAbstractUser
)
DMessageableChannel = DTextChannel | DVoiceChannel | DStageChannel | DThread \
  | DDMChannel | DPartialMessageable | DGroupChannel
from discord.app_commands import (
  Command             as DCommand,
  ContextMenu         as DContextMenu
)
from discord.client import _log
from discord.embeds import (
  EmbedProxy          as DEmbedProxy
)
from discord.raw_models import (
  RawAppCommandPermissionsUpdateEvent as DRawAppCommandPermissionsUpdateEvent,
  RawBulkMessageDeleteEvent           as DRawBulkMessageDeleteEvent,
  RawIntegrationDeleteEvent           as DRawIntegrationDeleteEvent,
  RawMemberRemoveEvent                as DRawMemberRemoveEvent,
  RawMessageDeleteEvent               as DRawMessageDeleteEvent,
  RawMessageUpdateEvent               as DRawMessageUpdateEvent,
  RawReactionActionEvent              as DRawReactionActionEvent,
  RawReactionClearEvent               as DRawReactionClearEvent,
  RawReactionClearEmojiEvent          as DRawReactionClearEmojiEvent,
  RawThreadDeleteEvent                as DRawThreadDeleteEvent,
  RawThreadMembersUpdate              as DRawThreadMembersUpdate,
  RawThreadUpdateEvent                as DRawThreadUpdateEvent,
  RawTypingEvent                      as DRawTypingEvent
)

from PyQt6.QtCore import (
  pyqtProperty,             pyqtSignal,
  QDir,                     QEasingCurve,
  QEvent,                   QFile,
  QMargins,                 QMetaObject,
  QMimeData,                QObject,
  QParallelAnimationGroup,  QPoint,
  QPointF,                  QPropertyAnimation,
  QRect,                    QRectF,
  QSettings,                QSize,
  Qt,                       QTime,
  QTimerEvent,              QUrl
)
from PyQt6.QtGui import (
  QBrush,                   QColor,
  QDrag,                    QDragEnterEvent,
  QDragMoveEvent,           QDropEvent,
  QIcon,                    QImage,
  QImageReader,             QResizeEvent,
  QFontDatabase,            QFontMetrics,
  QMouseEvent,              QPainter,
  QPainterPath,             QPixmap,
  QPolygonF,                QTextOption,
  QTransform,               QWheelEvent
)
from PyQt6.QtMultimedia import (
  QMediaPlayer,             QMediaMetaData
)
from PyQt6.QtMultimediaWidgets import (
  QVideoWidget
)
from PyQt6.QtNetwork import (
  QNetworkAccessManager,    QNetworkRequest
)
from PyQt6.QtSvgWidgets import (
  QSvgWidget
)
from PyQt6.QtWidgets import (
  QAbstractButton,          QApplication,
  QButtonGroup,             QGraphicsColorizeEffect,
  QGraphicsEffect,          QGraphicsOpacityEffect,
  QGridLayout,              QHBoxLayout,
  QLabel,                   QLayout,
  QPushButton,              QScrollBar,
  QSizePolicy,              QStackedLayout,
  QVBoxLayout,              QWidget
)

from . import resources
root = QDir(dirname(resources.__file__))
QDir.addSearchPath('root', root.absolutePath())
QDir.addSearchPath('local', root.absoluteFilePath('local'))
from .pure_extensions import *

T, U, V = TypeVar('T'), TypeVar('U'), TypeVar('V')
QConnection = QMetaObject.Connection
class Signal(Protocol):
  def connect(self, slot: Callable[[], None]) -> QConnection: ...
  def emit(self) -> None: ...
class Signal_(Protocol[T]):
  def connect(self, slot: Callable[[T], None]) -> QConnection: ...
  def emit(self, arg: T) -> None: ...
class Signal__(Protocol[T, U]):
  def connect(self, slot: Callable[[T, U], None]) -> QConnection: ...
  def emit(self, arg1: T, arg2: U) -> None: ...
class Signal___(Protocol[T, U, V]):
  def connect(self, slot: Callable[[T, U, V], None]) -> QConnection: ...
  def emit(self, arg1: T, arg2: U, arg3: V) -> None: ...

class QSignals(QObject):

  guild_selected: Signal_[DGuild | None] = pyqtSignal(object)
  '''
  Called whenever a new guild is selected.

  ## Parameters
  - guild - The newly selected guild. `None` represents the DM menu.
  '''

  channel_selected: Signal_[DMessageableChannel | None] = pyqtSignal(object)
  '''
  Called whenever a new channel is selected.

  ## Parameters
  - channel - The newly selected channel. `None` means no channel is available.
  '''

  tooltip_summons: Signal_[TooltipSummons | None] = pyqtSignal(object)
  '''
  Called whenever the tooltip is summoned or dismissed.

  ## Parameters
  - summons - The tooltip summons. `None` means the tooltip is dismissed.
  '''

  typing_registry_update: Signal = pyqtSignal()
  '''
  Called whenever a user starts or stops typing. This could be due to:
  - A user starts typing
  - 10 seconds have elapsed since a user last started typing
  - A typing user sends a message
  '''

  dm_registry_update: Signal = pyqtSignal()
  '''
  Called whenever the DM registry updates. This occurs when:
  - The client logs in and the app checks for new messages
  - The client receives a new message in real time
  '''

class AppState:

  def __init__(self) -> None:
    super().__init__()
    self._settings = Settings(root.absoluteFilePath('settings.ini'))
    self.guild_ordering = self._settings.read_array('guild-ordering')
    self.last_guild_id = self._settings.value('last-guild-id', 0)
    self.last_channel_id = self._settings.read_dict('last-channel-id')
    self.last_message_id = self._settings.read_dict('last-message-id')
    self.dm_list = self._settings.read_array('open-dms')

    self.selected_guild: DGuild | None = None
    self.selected_channel: DMessageableChannel | None = None
    self.tooltip_owner: QWidget | None = None
    self.dm_history: dict[int, tuple[DMessage, DMember]] = {}

    dsignals.on_ready.connect(self.on_ready)
    qsignals.guild_selected.connect(self.guild_selected)
    qsignals.channel_selected.connect(self.channel_selected)
    qsignals.tooltip_summons.connect(self.tooltip_summons)
    QAPP.aboutToQuit.connect(self.save)

  def save(self) -> None:
    _log.info('saving state')
    self._settings.write_array('guild-ordering', self.guild_ordering)
    self._settings.setValue('last-guild-id', self.last_guild_id)
    self._settings.write_dict('last-channel-id', self.last_channel_id)
    self._settings.write_dict('last-message-id', self.last_message_id)
    self._settings.write_array('open-dms', self.dm_list)
    self._settings.sync()

  def on_ready(self) -> None:
    priority: list[DMember] = []
    remaining: list[DMember] = []
    for user in client.users:
      if not user.bot:
        member = user.mutual_guilds[0].get_member(user.id)
        (priority if member.id in self.dm_list else remaining).append(member)
    client.submit(self.retrieve_dm_history(priority))
    client.submit(self.retrieve_dm_history(remaining))
    
  async def retrieve_dm_history(self, members: Iterable[DMember]) -> None:
    self.dm_history.update({
      member.id: (message, member) for member in members
      if (message := await anext(member.history(limit=1), None))
    })
    key = lambda id: self.dm_history[id][0].created_at.timestamp()
    dm_list = sorted(self.dm_history, key=key, reverse=True)
    if dm_list != self.dm_list:
      self.dm_list.extend(dm_list)
    qsignals.dm_registry_update.emit()
  
  def guild_selected(self, guild: DGuild | None) -> None:
    self.selected_guild = guild
    self.last_guild_id = guild.id if guild else 0

  def channel_selected(self, channel: DMessageableChannel | None) -> None:
    self.selected_channel = channel
    self.last_channel_id[self.last_guild_id] = channel.id if channel else 0
  
  def tooltip_summons(self, summons: TooltipSummons | None) -> None:
    self.tooltip_owner = summons.owner if summons else None
  
class Discord:

  def run(self) -> None:
    client.thread.start()
    current_thread().name = 'Qt GUI Thread'

    QAPP.exec()

    client.submit(client.close())

from discord import utils
utils.valid_icon_size = lambda _: True

QAPP = QApplication(argv)
assert load_dotenv(root.absoluteFilePath('token.env'))
assert (TOKEN := getenv('TOKEN'))
for font in QDir(root.absoluteFilePath('fonts')).entryInfoList():
  QFontDatabase.addApplicationFont(font.absoluteFilePath())

discord = Discord()
qsignals = QSignals()
from ._css import *
from ._bridge import *
state = AppState()
from .Registrar import *

from ._utils import *
ui: 'DiscordWindow' = None
from .DiscordUI import DiscordWindow
ui = DiscordWindow()
# from .annoying import *
