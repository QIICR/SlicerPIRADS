import qt
import os
import slicer

class ProstateSectorMapDialog(object):

  def __init__(self):
    self.modulePath = os.path.dirname(slicer.util.modulePath("SlicerPIRADS"))
    self.setup()

  def setup(self):
    path = os.path.join(self.modulePath, 'Resources', 'UI', 'ProstateSectorMapDialog.ui')
    self.ui = slicer.util.loadUI(path)
    self._backgroundLabel = self.ui.findChild(qt.QLabel, "prostateSectorMap")
    self._sectorButtonGroup = self.ui.findChild(qt.QButtonGroup, "sectorButtonGroup")
    self._dialogButtonBox = self.ui.findChild(qt.QDialogButtonBox, "dialogButtonBox")
    icon = qt.QIcon(os.path.join(self.modulePath, 'Resources', 'Images', 'prostate_sector_map.png'))
    self._backgroundLabel.setPixmap(icon.pixmap(qt.QSize(500, 683)))
    self._setupConnections()

  def exec_(self):
    return self.ui.exec_()

  def _setupConnections(self):
    self._dialogButtonBox.clicked.connect(self._onButtonClicked)

  def getSelectedSectors(self):
    return [b.objectName for b in self._sectorButtonGroup.buttons() if b.checked]

  def setSelectedSectors(self, sectors):
    for b in self._sectorButtonGroup.buttons():
      b.checked = b.objectName in sectors

  def resetButtons(self):
    for b in self._sectorButtonGroup.buttons():
      b.checked = False

  def _onButtonClicked(self, button):
    if self._dialogButtonBox.buttonRole(button) == qt.QDialogButtonBox.ResetRole:
      self.resetButtons()