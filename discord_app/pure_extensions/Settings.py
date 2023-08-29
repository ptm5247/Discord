from discord_app import QSettings

class Settings(QSettings):

  def __init__(self, file_path: str) -> None:
    super().__init__(file_path, self.Format.IniFormat)

  def value(self, key: str, default=None, from_str=None) -> ...:
    value = super().value(key, default)
    return from_str(value) if from_str else value
  
  def write_array(self, name: str, array: list) -> None:
    self.beginWriteArray(name)
    for i, e in enumerate(array):
      self.setArrayIndex(i)
      self.setValue('li', e)
    self.endArray()

  def read_array(self, name: str, from_str=int) -> list:
    array = []
    for i in range(self.beginReadArray(name)):
      self.setArrayIndex(i)
      array.append(from_str(self.value('li')))
    self.endArray()
    return array
  
  def write_dict(self, name: str, dict: dict) -> None:
    self.beginGroup(name)
    for k, v in dict.items():
      self.setValue(str(k), v)
    self.endGroup()

  def read_dict(self, name: str, from_str=int) -> dict:
    self.beginGroup(name)
    dict = { k: from_str(self.value(k))
             for k in self.childKeys() }
    self.endGroup()
    return dict
  
__all__ = ['Settings']
