import qt
import vtk
import os
import slicer
import logging

from SlicerDevelopmentToolboxUtils.mixins import GeneralModuleMixin

from SlicerPIRADSLogic.Finding import Finding
from SlicerPIRADSLogic.SeriesType import SeriesTypeFactory
from SlicerPIRADSWidgets.AnnotationWidget import AnnotationWidgetFactory, AnnotationItemWidget
from SlicerPIRADSWidgets.ProstateSectorMapDialog import ProstateSectorMapDialog


class FindingsWidget(qt.QWidget, GeneralModuleMixin):

  def __init__(self, maximumNumber=None, parent=None):
    qt.QWidget.__init__(self, parent)
    self.modulePath = os.path.dirname(slicer.util.modulePath("SlicerPIRADS"))
    self._maximumFindingCount = maximumNumber
    self.setup()

  def setup(self):
    self._findingInformationWidget = None

    self.setLayout(qt.QGridLayout())
    self._loadUI()
    self.layout().addWidget(self.ui)
    self._setupConnections()

  def _loadUI(self):
    path = os.path.join(self.modulePath, 'Resources', 'UI', 'FindingsWidget.ui')
    self.ui = slicer.util.loadUI(path)
    self._addFindingsButton = self.ui.findChild(qt.QPushButton, "addFindingsButton")
    self._removeFindingsButton = self.ui.findChild(qt.QPushButton, "removeFindingsButton")
    self._titleLabel = self.ui.findChild(qt.QLabel, "titleLabel")
    self._findingsListView = self.ui.findChild(qt.QListView, "findingsListView")
    self._findingsListModel = FindingsListModel()
    self._findingsListView.setModel(self._findingsListModel)
    self._updateButtons()

  def _setupConnections(self):
    def setupConnections(funcName="connect"):
      getattr(self._addFindingsButton.clicked, funcName)(self._onAddFindingsButtonClicked)
      getattr(self._removeFindingsButton.clicked, funcName)(self._onRemoveFindingRequested)
      getattr(self._findingsListView, funcName)("customContextMenuRequested(QPoint)", self._onFindingItemRightClicked)
      getattr(self._findingsListView.selectionModel(), funcName)("currentRowChanged(QModelIndex, QModelIndex)",
                                                                  self._onFindingSelectionChanged)

    setupConnections()
    slicer.app.connect('aboutToQuit()', self.deleteLater)
    self.destroyed.connect(lambda : setupConnections(funcName="disconnect"))

  def _onFindingItemRightClicked(self, point):
    if not self._findingsListView.currentIndex() or not self._findingsListView.model().rowCount():
      return
    self.listMenu = qt.QMenu()
    menu_item = self.listMenu.addAction("Remove Item")
    menu_item.triggered.connect(self._onRemoveFindingRequested)
    parentPosition = self._findingsListView.mapToGlobal(qt.QPoint(0, 0))
    self.listMenu.move(parentPosition + point)
    self.listMenu.show()

  def _onRemoveFindingRequested(self):
    currentIndex = self._findingsListView.currentIndex()
    finding = self._findingsListModel.getFindings()[currentIndex.row()]
    if slicer.util.confirmYesNoDisplay("Finding '{}' is about to be deleted. "
                                       "Do you want to proceed?".format(finding.getName())):
      self._findingsListModel.removeFinding(finding)
      self._deleteFindingInformationWidget()
      self._updateButtons()

  def _onAddFindingsButtonClicked(self):
    # TODO: findings assessment
    import random
    finding = Finding("Finding %s" %random.randint(0,10))
    self._findingsListModel.addFinding(finding)
    self._findingsListView.selectionModel().clear()
    model = self._findingsListView.model()
    self._findingsListView.selectionModel().setCurrentIndex(model.index(model.rowCount() - 1, 0),
                                                            qt.QItemSelectionModel.Select)
    self._updateButtons()

  def _onFindingSelectionChanged(self, current, previous):
    self._deleteFindingInformationWidget()

    row = current.row()
    if row >= 0:
      finding =  self._findingsListModel.getFindings()[row]
      # TODO: jump to centroid of lesion
      self._displayFindingInformationWidget(finding)

    self._updateButtons()

  def _displayFindingInformationWidget(self, finding):
    if not self._findingInformationWidget:
      self._findingInformationWidget = FindingInformationWidget(finding)
    else:
      self._findingInformationWidget.setFinding(finding)
    self._findingInformationWidget.show()
    self.ui.layout().addWidget(self._findingInformationWidget)

  def _deleteFindingInformationWidget(self):
    if self._findingInformationWidget:
      self.ui.layout().removeWidget(self._findingInformationWidget)
      self._findingInformationWidget.hide()

  def _updateButtons(self):
    currentIndex = self._findingsListView.currentIndex()
    self._removeFindingsButton.setEnabled(self._findingsListView.selectedIndexes()
                                          and self._findingsListModel.rowCount() > 0)
    self._addFindingsButton.setEnabled(self._findingsListModel.rowCount() < self._maximumFindingCount)


class FindingsListModel(qt.QAbstractListModel):

  def __init__(self, parent=None, *args):
    qt.QAbstractListModel.__init__(self, parent, *args)
    self._findings = list()

  def getFindings(self):
    return self._findings

  def addFinding(self, finding):
    self._findings.append(finding)
    finding.addEventObserver(finding.DataChangedEvent, lambda caller, event: self._onFindingDataChanged(finding))
    self.dataChanged(self.index(self.rowCount()-1, 0), self.index(self.rowCount()-1, 0))

  def removeFinding(self, finding):
    assert finding in self._findings
    row = self._findings.index(finding)
    self._findings.pop(row)
    self.removeRow(row)

  def rowCount(self):
    return len(self._findings)

  def data(self, index, role):
    if role != qt.Qt.DisplayRole:
      return None
    return self._findings[index.row()].getName()

  def _onFindingDataChanged(self, finding):
    row = self._findings.index(finding)
    self.dataChanged(self.index(row, 0), self.index(row, 0))


class FindingInformationWidget(qt.QWidget):

  def __init__(self, finding, parent=None):
    qt.QWidget.__init__(self, parent)
    self._finding = finding
    self.modulePath = os.path.dirname(slicer.util.modulePath("SlicerPIRADS"))
    self._volumeNodes = slicer.util.getNodesByClass('vtkMRMLScalarVolumeNode')
    self.setup()

  def setFinding(self, finding):
    self._finding = finding
    self._fillAnnotationTable()
    self._removeAnnotationToolWidget()

  def setup(self):
    self.setLayout(qt.QGridLayout())
    self._loadUI()
    self.layout().addWidget(self.ui)
    self._setupConnections()

  def _loadUI(self):
    path = os.path.join(self.modulePath, 'Resources', 'UI', 'FindingInformationWidget.ui')
    self.ui = slicer.util.loadUI(path)
    self._findingNameEdit = self.ui.findChild(qt.QLineEdit, "findingsNameEdit")
    self._findingNameEdit.text = self._finding.getName()
    self._prostateMapButton = self.ui.findChild(qt.QPushButton, "prostateMapButton")
    self._prostateMapButton.setIconSize(qt.QSize(20, 32))
    self._prostateMapButton.setIcon(qt.QIcon(os.path.join(self.modulePath, 'Resources', 'Icons', 'ProstateMap.png')))
    self._prostateMapDialog = None
    self._annotationListWidget = self.ui.findChild(qt.QListWidget, "annotationsListWidget")
    self._annotationToolFrame = self.ui.findChild(qt.QFrame, "annotationToolFrame")
    self._annotationToolFrame.setLayout(qt.QGridLayout())
    self._currentAnnotationToolWidget = None
    self._annotationToolWidgets = dict()
    self._fillAnnotationTable()

  def _setupConnections(self):
    self._annotationListWidget.connect("currentItemChanged(QListWidgetItem *, QListWidgetItem *)",
                                       self._onCurrentItemChanged)
    self._findingNameEdit.textChanged.connect(self._onFindingNameChanged)
    self._prostateMapButton.clicked.connect(self._onProstateMapButtonClicked)
    self.destroyed.connect(self._cleanupConnections)

  def _onCurrentItemChanged(self, current, previous):
    if current:
      self._annotationListWidget.itemWidget(current).enable(True)
    if previous:
      self._annotationListWidget.itemWidget(previous).enable(False)
      self._removeAnnotationToolWidget()

  def _onFindingNameChanged(self, text):
    # TODO: what to do with empty string?
    self._finding.setName(text)

  def _cleanupConnections(self):
    self._prostateMapButton.clicked.disconnect(self._onProstateMapButtonClicked)

  def _fillAnnotationTable(self):
    self._annotationListWidget.clear()
    for volume in self._volumeNodes:
      seriesType = SeriesTypeFactory.getSeriesType(volume)
      if seriesType:
        listWidgetItem = qt.QListWidgetItem(self._annotationListWidget)
        self._annotationListWidget.addItem(listWidgetItem)

        annotationItemWidget = AnnotationItemWidget(self._finding, seriesType(volume))
        annotationItemWidget.addEventObserver(annotationItemWidget.AnnotationToolSelectedEvent,
                                              self.onAnnotationToolSelected)
        annotationItemWidget.addEventObserver(annotationItemWidget.AnnotationToolDeselectedEvent,
                                              lambda caller, event: self._removeAnnotationToolWidget())
        listWidgetItem.setSizeHint(annotationItemWidget.sizeHint)
        self._annotationListWidget.setItemWidget(listWidgetItem, annotationItemWidget)
      else:
        logging.info("Could not find matching series type for volume %s" % volume.GetName())

  @vtk.calldata_type(vtk.VTK_STRING)
  def onAnnotationToolSelected(self, caller, event, callData):
    itemWidget = self.getAnnotationItemWidgetForParameterNode(caller)
    assert itemWidget
    self._removeAnnotationToolWidget()
    seriesType = itemWidget.getSeriesType()
    annotation = self._finding.getOrCreateAnnotation(seriesType, callData)
    try:
      annotationWidgetClass = AnnotationWidgetFactory.getAnnotationWidgetForMRMLNode(annotation.mrmlNode)
      self._currentAnnotationToolWidget = self._getOrCreateAnnotationToolWidget(annotationWidgetClass, seriesType)
    except AttributeError:
      pass

  def getAnnotationItemWidgetForParameterNode(self, pNode):
    for idx in range(self._annotationListWidget.count):
      item = self._annotationListWidget.item(idx)
      widget = self._annotationListWidget.itemWidget(item)
      if widget.parameterNode is pNode:
        return widget
    return None

  def _onProstateMapButtonClicked(self):
    if not self._prostateMapDialog:
      self._prostateMapDialog = ProstateSectorMapDialog()

    self._prostateMapDialog.setSelectedSectors(self._finding.getSectors())

    if self._prostateMapDialog.exec_():
      self._finding.setSectors(self._prostateMapDialog.getSelectedSectors())

  def _removeAnnotationToolWidget(self):
    # TODO: this is too specific for the segment editor
    if self._currentAnnotationToolWidget:
      self._currentAnnotationToolWidget.resetInteraction()
      self._annotationToolFrame.layout().removeWidget(self._currentAnnotationToolWidget.editor)
      self._currentAnnotationToolWidget = None

  def _getOrCreateAnnotationToolWidget(self, annotationWidgetClass, seriesType):
    try:
      annotationWidget = self._annotationToolWidgets[annotationWidgetClass]
      annotationWidget.setData(self._finding, seriesType)
      annotationWidget.parent = self._annotationToolFrame
      self._annotationToolFrame.layout().addWidget(annotationWidget.editor)
    except KeyError:
      annotationWidget = annotationWidgetClass(parent=self._annotationToolFrame, finding=self._finding,
                                               seriesType=seriesType)
      self._annotationToolWidgets[annotationWidgetClass] = annotationWidget
    return annotationWidget