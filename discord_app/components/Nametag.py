from discord_app import (
  QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget,
  registrar, client
)

class Nametag(QWidget):
  '''The widget in the bottom left displaying the client's profile'''

  def __init__(self, parent: QWidget) -> None:
    super().__init__(parent, layout=QHBoxLayout)

    self.user = ClientUser(self)
    mute = QPushButton(self, name='MuteButton')
    deafen = QPushButton(self, name='DeafenButton')
    mute.setCheckable(True)
    deafen.setCheckable(True)

    self.layout().addWidget(self.user)
    self.layout().addSpacing(8)
    self.layout().addWidget(mute)
    self.layout().addWidget(deafen)

class ClientUser(QWidget):

  def __init__(self, parent: QWidget) -> None:
    super().__init__(parent, layout=QHBoxLayout)

    self.avatar = registrar.Avatar(self, False, False, False)
    self.username = QLabel(self, name='Username')
    self.discriminator = QLabel(self, name='Discriminator')

    self.layout().addWidget(self.avatar)
    self.layout().addSpacing(-4)
    self.layout().addLayout(text_container := QVBoxLayout())
    text_container.addWidget(self.username)
    text_container.addWidget(self.discriminator)

  def update_information(self) -> None:
    self.avatar.set_asset(client.user)
    self.avatar.set_status(client.status, True)
    self.username.setText(client.user.name)
    self.discriminator.setText('#' + client.user.discriminator)
