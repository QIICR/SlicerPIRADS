import ctk
import os
import slicer
import qt
from random import random


from SlicerDevelopmentToolboxUtils.mixins import GeneralModuleMixin
from SlicerPIRADSLogic.Finding import Finding


class ProstateWidget(ctk.ctkCollapsibleButton, GeneralModuleMixin):

  def __init__(self, parent=None):
    ctk.ctkCollapsibleButton.__init__(self, parent)
    self.text = "Prostate Gland Measurements"
    self.modulePath = os.path.dirname(slicer.util.modulePath("SlicerPIRADS"))
    self.setup()

  def setup(self):
    self.setLayout(qt.QGridLayout())
    self._loadUI()
    self.layout().addWidget(self.ui)
    self._setupConnections()

  def _loadUI(self):
    path = os.path.join(self.modulePath, 'Resources', 'UI', 'ProstateWidget.ui')
    self.ui = slicer.util.loadUI(path)
    self._addMeasurementsButton = self.ui.findChild(qt.QPushButton, "addMeasurementButton")
    self._addMenu(self._addMeasurementsButton)
    self._measurementsListWidget = self.ui.findChild(qt.QListWidget, "listWidget")
    self._updateButtons()

  def _addMenu(self, button):
    menu = qt.QMenu(button)
    menu.name = button.name
    button.setMenu(menu)

    actionGroup = qt.QActionGroup(menu)
    actionGroup.setExclusive(False)

    for name, enabled in [("Linear Measurement", True), ("Volumetric Measurement", False)]:
      action = qt.QAction(name, actionGroup)
      action.setEnabled(enabled)
      menu.addAction(action)
      actionGroup.addAction(action)
      action.triggered.connect(lambda triggered, a=action: self._onActionTriggered(a))

  def _onActionTriggered(self, action):
    action.setEnabled(False)

    # Depending on type
    finding = Finding("Finding %s" % random.randint(0, 10))
    self._findingsListModel.addFinding(finding)
    self._measurementsListWidget.selectionModel().clear()
    model = self._measurementsListWidget.model()
    self._measurementsListWidget.selectionModel().setCurrentIndex(model.index(model.rowCount() - 1, 0),
                                                                  qt.QItemSelectionModel.Select)
    self._updateButtons()

  def _setupConnections(self):
    def setupConnections(funcName="connect"):
      getattr(self._measurementsListWidget, funcName)("customContextMenuRequested(QPoint)", self._onFindingItemRightClicked)
      getattr(self._measurementsListWidget.selectionModel(), funcName)("currentRowChanged(QModelIndex, QModelIndex)",
                                                                       self._onFindingSelectionChanged)

    setupConnections()
    slicer.app.connect('aboutToQuit()', self.deleteLater)
    self.destroyed.connect(lambda : setupConnections(funcName="disconnect"))

  def _onFindingItemRightClicked(self, point):
    if not self._measurementsListWidget.currentIndex() or not self._measurementsListWidget.model().rowCount():
      return
    self.listMenu = qt.QMenu()
    menu_item = self.listMenu.addAction("Remove Item")
    menu_item.triggered.connect(self._onRemoveFindingRequested)
    parentPosition = self._measurementsListWidget.mapToGlobal(qt.QPoint(0, 0))
    self.listMenu.move(parentPosition + point)
    self.listMenu.show()

  def _onRemoveFindingRequested(self):
    currentIndex = self._measurementsListWidget.currentIndex()
    finding = self._findingsListModel.getFindings()[currentIndex.row()]
    if slicer.util.confirmYesNoDisplay("Finding '{}' is about to be deleted. "
                                       "Do you want to proceed?".format(finding.getName())):
      self._findingsListModel.removeFinding(finding)
      self._deleteFindingInformationWidget()
      self._updateButtons()

  def _onFindingSelectionChanged(self, current, previous):
    self._deleteFindingInformationWidget()

    row = current.row()
    if row >= 0:
      finding =  self._findingsListModel.getFindings()[row]
      # TODO: jump to centroid of lesion

    self._updateButtons()

  def _onAddFindingsButtonClicked(self):
    # TODO: findings assessment
    # TODO: add segmentation and enable editor
    listWidgetItem = qt.QListWidgetItem(self._measurementsListWidget)
    self._measurementsListWidget.addItem(listWidgetItem)
    findingsItemWidget = ProstateMeasurementItemWidget()
    listWidgetItem.setSizeHint(findingsItemWidget.sizeHint)
    self._findingsListWidget.setItemWidget(listWidgetItem, findingsItemWidget)

    self._findingsListWidget.selectionModel().clear()
    model = self._findingsListWidget.model()
    self._findingsListWidget.selectionModel().setCurrentIndex(model.index(model.rowCount()-1, 0),
                                                              qt.QItemSelectionModel.Select)

    self.updateButtons()

  def _updateButtons(self):
    pass
    # self._addMeasurementsButton.setEnabled(self._findingsListModel.rowCount() < self._maximumFindingCount)


class ProstateMeasurementItemWidget(qt.QWidget):

  def __init__(self):
    super(ProstateMeasurementItemWidget, self).__init__()
    self.modulePath = os.path.dirname(slicer.util.modulePath("SlicerPIRADS"))
    self.setup()
    self._processData()

  def setup(self):
    self.setLayout(qt.QGridLayout())
    path = os.path.join(self.modulePath, 'Resources', 'UI', 'ProstateMeasurementItemWidget.ui')
    self.ui = slicer.util.loadUI(path)

    self._measurementIconLabel = self.ui.findChild(qt.QLabel, "measurementTypeLabel")
    self._measurementLabel = self.ui.findChild(qt.QLabel, "measurementLabel")

    self.layout().addWidget(self.ui)

  def _processData(self):
    return
    icon = self._finding.getIcon()
    # self._measurementTypeLabel.setPixmap(icon.pixmap(qt.QSize(32, 32)))
    #
    # self._findingNameLabel.text = self._finding.getName()
    # self._locationLabel.text = self._finding.getLocation()
    # self._measurementLabel.text = str(self._finding.getMeasurementValue())