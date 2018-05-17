import qt
import os
import slicer


class ScreenShotMixin(object):

  SV_RECT = qt.QRect(260, 0, 240, 105)
  BASE_RECT = qt.QRect(270, 105, 230, 165)
  MID_RECT = qt.QRect(290, 280, 210, 165)
  APEX_RECT = qt.QRect(310, 465, 190, 130)
  UR_RECT = qt.QRect(355, 610, 145,65 )

  REGIONS = {"Vesicle": SV_RECT, "Base": BASE_RECT, "Mid": MID_RECT, "Apex": APEX_RECT, "Urethra": UR_RECT}

  def getScreenShots(self):
    pixmaps = []
    for rect in self.getRegionRectangles():
      pixmap = qt.QPixmap(rect.size())
      self.ui.render(pixmap, qt.QPoint(), qt.QRegion(rect))
      pixmaps.append(pixmap)
    return pixmaps

  def getRegionRectangles(self):
    selectedRegions = set([sector.split("_")[1] for sector in self.getSelectedSectors()])
    return [self.REGIONS[selRegion] for selRegion in selectedRegions]


class ProstateSectorMapDialog(ScreenShotMixin):

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