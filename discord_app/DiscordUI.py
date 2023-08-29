import ctypes

from discord_app import (
  QWidget, QStackedLayout, QIcon, QPushButton, QGridLayout, QPropertyAnimation,
  Qt, QGraphicsOpacityEffect, QVideoWidget, QMediaPlayer, QUrl, QMediaMetaData,
  Tooltip, qsignals, dsignals
)

from .components import GuildList, NavigationPane, Nametag, ChannelScreen
from ._css import FloatProperty

DWMWA_USE_IMMERSIVE_DARK_MODE = 20

class DiscordWindow(QWidget):

  def __init__(self) -> None:
    super().__init__(layout=QStackedLayout)

    ctypes.windll.dwmapi.DwmSetWindowAttribute(
      int(self.winId()), DWMWA_USE_IMMERSIVE_DARK_MODE,
      ctypes.byref(ctypes.c_int(1)), ctypes.sizeof(ctypes.c_int(1))
    )

    self.resize(1100, 580)
    window_rect = self.frameGeometry()
    window_rect.moveCenter(self.screen().availableGeometry().center())
    self.move(window_rect.topLeft())

    self.setWindowTitle('Discord')
    self.setWindowIcon(QIcon('local:discord.png'))

    self.main_window = DiscordUI(self)
    self.loading_screen = LoadingScreen(self)
    self.popup_window = QPushButton(self, layout=QGridLayout, name='Popup')
    self.popup_window.setCheckable(True)
    animation: QPropertyAnimation = \
      self.popup_window.__style__.transitions['background'][1]
    animation.finished.connect(self.hide_popup)

    self.layout().setStackingMode(QStackedLayout.StackingMode.StackAll)
    self.layout().addWidget(self.loading_screen)
    self.layout().addWidget(self.main_window)
    self.layout().addWidget(self.popup_window)

    dsignals.on_ready.connect(
      self.api_ready, Qt.ConnectionType.SingleShotConnection
    )
    self.show()

  def show_popup(self, popup: QWidget) -> None:
    self.popup_window.layout().addWidget(popup)
    self.layout().setCurrentWidget(self.popup_window)
    self.popup_window.setChecked(True)

  def hide_popup(self) -> None:
    if not self.popup_window.isChecked():
      if self.layout().currentWidget() is self.popup_window:
        self.layout().setCurrentWidget(self.main_window)
      while self.popup_window.layout():
        self.popup_window.layout().takeAt(0).widget().deleteLater()
  
  def api_ready(self) -> None:
    self.loading_screen.player.positionChanged.connect(self.loading_position)

  def loading_position(self, pos: int) -> None:
    if pos == 0:
      self.loading_screen.player.pause()
      self.loading_screen.content.hide()

      self.main_window.nametag.user.update_information()
      self.main_window.guild_list.fill()

      property = FloatProperty(self.loading_screen, 1.)
      opacity = QGraphicsOpacityEffect()
      opacity.setOpacity(property.value)
      self.loading_screen.setGraphicsEffect(opacity)
      fade = QPropertyAnimation(property, property.NAME, self)
      fade.setEndValue(0)
      fade.setDuration(500)
      fade.valueChanged.connect(opacity.setOpacity)
      fade.finished.connect(self.loading_screen.deleteLater)
      fade.start()

class LoadingScreen(QWidget):

  def __init__(self, parent: DiscordWindow) -> None:
    super().__init__(parent, layout=QGridLayout)

    self.content = QVideoWidget(self)
    self.player = QMediaPlayer(self)
    self.player.setSource(QUrl.fromLocalFile('local:loading.mp4'))
    self.player.setVideoOutput(self.content)
    self.player.setLoops(QMediaPlayer.Loops.Infinite)

    self.layout().addWidget(self.content)

    self.player.mediaStatusChanged.connect(self.media_status_changed)

  def media_status_changed(self, status: QMediaPlayer.MediaStatus) -> None:
    if status is QMediaPlayer.MediaStatus.LoadedMedia:
      size = self.player.metaData().value(QMediaMetaData.Key.Resolution)
      self.content.setFixedSize(size)
      self.player.play()

class DiscordUI(QWidget):

  def __init__(self, parent: DiscordWindow):
    super().__init__(parent, layout=QGridLayout)

    grid: QGridLayout = self.layout()
    grid.setColumnStretch(2, 1)
    grid.setRowStretch(0, 1)

    self.guild_list = GuildList(self)
    self.navigation_pane = NavigationPane(self)
    self.nametag = Nametag(self)
    self.channel_screen = ChannelScreen(self)
    self.tooltip = Tooltip(self)

    grid.addWidget(self.guild_list, 0, 0, 2, 1)
    grid.addWidget(self.navigation_pane, 0, 1)
    grid.addWidget(self.nametag, 1, 1)
    grid.addWidget(self.channel_screen, 0, 2, 2, 1)

    qsignals.tooltip_summons.connect(self.tooltip.summon)
