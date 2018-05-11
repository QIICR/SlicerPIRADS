import qt
import vtk
import ctk
import os
import slicer
import logging

from SlicerDevelopmentToolboxUtils.mixins import GeneralModuleMixin, ModuleWidgetMixin
from SlicerDevelopmentToolboxUtils.icons import Icons
from SlicerDevelopmentToolboxUtils.decorators import onExceptionReturnNone

from SlicerPIRADSLogic.Finding import Finding
from SlicerPIRADSLogic.SeriesType import SeriesTypeFactory
from SlicerPIRADSLogic.PIRADSAssessmentCategory import PIRADSAssessmentCategory
from SlicerPIRADSWidgets.AnnotationWidget import AnnotationWidgetFactory, AnnotationItemWidget
from SlicerPIRADSWidgets.ProstateSectorMapDialog import ProstateSectorMapDialog


class FindingsWidget(ctk.ctkCollapsibleButton, GeneralModuleMixin):

  def __init__(self, maximumNumber=None, parent=None):
    ctk.ctkCollapsibleButton.__init__(self, parent)
    self.text = "Findings"
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
    self._prostateMapDialog = None
    self._addFindingsButton = self.ui.findChild(qt.QPushButton, "addFindingsButton")
    self._removeFindingsButton = self.ui.findChild(qt.QPushButton, "removeFindingsButton")
    self._titleLabel = self.ui.findChild(qt.QLabel, "titleLabel")
    self._findingsListView = self.ui.findChild(qt.QListView, "findingsListView")
    self._findingsListModel = FindingsListModel()
    self._findingsListView.setModel(self._findingsListModel)
    self._prostateMapButton = self.ui.findChild(qt.QPushButton, "prostateMapButton")
    self._prostateMapButton.setIcon(Icons.text_info)
    self._findingInformationFrame = self.ui.findChild(qt.QFrame, "findingInformationFrame")
    self._updateButtons()

  def _setupConnections(self):
    def setupConnections(funcName="connect"):
      getattr(self._prostateMapButton.clicked, funcName)(self._onProstateMapButtonClicked)
      getattr(self._addFindingsButton.clicked, funcName)(self._onAddFindingsButtonClicked)
      getattr(self._removeFindingsButton.clicked, funcName)(self._onRemoveFindingRequested)
      getattr(self._findingsListView, funcName)("customContextMenuRequested(QPoint)", self._onFindingItemRightClicked)
      getattr(self._findingsListView.selectionModel(), funcName)("currentRowChanged(QModelIndex, QModelIndex)",
                                                                  self._onFindingSelectionChanged)

    setupConnections()
    slicer.app.connect('aboutToQuit()', self.deleteLater)
    self.destroyed.connect(lambda : setupConnections(funcName="disconnect"))

  # def _onFindingNameChanged(self, text):
  #   # TODO: what to do with empty string?
  #   self._finding.setName(text)

  def _onProstateMapButtonClicked(self):
    row = self._findingsListView.currentIndex().row()
    if -1 < row < self._findingsListModel.rowCount():
      finding = self._findingsListModel.getFindings()[row]

      if not self._prostateMapDialog:
        self._prostateMapDialog = ProstateSectorMapDialog()
      self._prostateMapDialog.setSelectedSectors(finding.getSectors())

      if self._prostateMapDialog.exec_():
        # TODO:
        finding.setSectors(self._prostateMapDialog.getSelectedSectors())

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
    self._findingInformationFrame.layout().addWidget(self._findingInformationWidget)

  def _deleteFindingInformationWidget(self):
    if self._findingInformationWidget:
      self._findingInformationFrame.layout().removeWidget(self._findingInformationWidget)
      self._findingInformationWidget.hide()

  def _updateButtons(self):
    currentIndex = self._findingsListView.currentIndex()
    self._removeFindingsButton.setEnabled(self._findingsListView.selectedIndexes()
                                          and self._findingsListModel.rowCount() > 0)
    self._addFindingsButton.setEnabled(self._findingsListModel.rowCount() < self._maximumFindingCount)
    self._prostateMapButton.setEnabled(-1 < self._findingsListView.currentIndex().row() < self._findingsListModel.rowCount())


class FindingsListModel(qt.QAbstractListModel):

  def __init__(self, parent=None, *args):
    qt.QAbstractListModel.__init__(self, parent, *args)
    self._assessmentCategoryCalculator = PIRADSAssessmentCategory()

  def getFindings(self):
    return self._assessmentCategoryCalculator.getFindings()

  def addFinding(self, finding):
    self._assessmentCategoryCalculator.addFinding(finding)
    finding.addEventObserver(finding.DataChangedEvent, lambda caller, event: self._onFindingDataChanged(finding))
    self.dataChanged(self.index(self.rowCount()-1, 0), self.index(self.rowCount()-1, 0))

  def removeFinding(self, finding):
    index = self._assessmentCategoryCalculator.removeFinding(finding)
    self.removeRow(index)
    self.dataChanged(self.index(index, 0), self.index(index, 0))

  def rowCount(self):
    return len(self._assessmentCategoryCalculator)

  def data(self, index, role):
    if role != qt.Qt.DisplayRole:
      return None
    return self._assessmentCategoryCalculator.getFindings()[index.row()].getName()

  def _onFindingDataChanged(self, finding):
    row = self._assessmentCategoryCalculator.getFindings().index(finding)
    self.dataChanged(self.index(row, 0), self.index(row, 0))


class FindingInformationWidget(qt.QWidget):

  ICON_MAP = {"vtkMRMLSegmentationNode": "SegmentEditor.png",
              "vtkMRMLAnnotationRulerNode": "Ruler.png",
              "vtkMRMLMarkupFiducialNode": "Fiducials.png"}

  @staticmethod
  def getIconFromMRMLNodeClass(name):
    modulePath = os.path.dirname(slicer.util.modulePath("SlicerPIRADS"))
    return qt.QIcon(os.path.join(modulePath, 'Resources', 'Icons', FindingInformationWidget.ICON_MAP[name]))

  @staticmethod
  def getIconFromMRMLNode(mrmlNode):
    return FindingInformationWidget.getIconFromMRMLNodeClass(mrmlNode.__class__.__name__)

  def __init__(self, finding, parent=None):
    qt.QWidget.__init__(self, parent)
    self._finding = finding
    self.modulePath = os.path.dirname(slicer.util.modulePath("SlicerPIRADS"))
    self._volumeNodes = slicer.util.getNodesByClass('vtkMRMLScalarVolumeNode')
    self._seriesTypes = dict()
    self.setup()

  def setFinding(self, finding):
    # TODO: restore data
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
    self._annotationListWidget = self.ui.findChild(qt.QListWidget, "annotationsListWidget")
    self._annotationToolFrame = self.ui.findChild(qt.QFrame, "annotationToolFrame")
    self._annotationToolFrame.setLayout(qt.QGridLayout())
    self._annotationButtonGroup = self.ui.findChild(qt.QButtonGroup, "annotationButtonGroup")
    self._annotationButtonFrame = self.ui.findChild(qt.QFrame, "annotationButtonFrame")
    self._annotationButtonFrame.enabled = False
    for button in self._annotationButtonGroup.buttons():
      button.setIcon(self.getIconFromMRMLNodeClass(button.property("MRML_NODE_CLASS")))
    self._currentAnnotationToolWidget = None
    self._annotationToolWidgets = dict()
    self._fillAnnotationTable()

  def _setupConnections(self):
    self._annotationButtonGroup.connect("buttonToggled(QAbstractButton*, bool)", self._onAnnotationButtonClicked)
    self._annotationListWidget.itemSelectionChanged.connect(self._onItemSelectionChanged)
    self.destroyed.connect(self._cleanupConnections)

  def _cleanupConnections(self):
    self._annotationButtonGroup.disconnect("buttonToggled(QAbstractButton*, bool)", self._onAnnotationButtonClicked)

  def _onAnnotationButtonClicked(self, button, checked):
    currentItem = self._annotationListWidget.currentItem()
    if not currentItem:
      return
    itemWidget = self._annotationListWidget.itemWidget(currentItem)
    seriesType = itemWidget.getSeriesType()
    if checked:
      for b in self._annotationButtonGroup.buttons():
        if b.checked and b is not button:
          b.checked = False
      for w in ModuleWidgetMixin.getAllVisibleWidgets():
        enabled = w.mrmlSliceCompositeNode().GetForegroundVolumeID() is not None and seriesType.getVolume() is \
                  slicer.mrmlScene.GetNodeByID(w.mrmlSliceCompositeNode().GetForegroundVolumeID())
        w.enabled = enabled
        w.setStyleSheet("#frame{{border: 5px ridge {};}}".format("green" if enabled else "black"))
      self._onAnnotationToolSelected(seriesType, button.property("MRML_NODE_CLASS"))
    else:
      for w in ModuleWidgetMixin.getAllVisibleWidgets():
        w.enabled = True
        w.setStyleSheet("")
      self._onAnnotationToolDeselected(seriesType, button.property("MRML_NODE_CLASS"))

  def _onItemSelectionChanged(self):
    currentItem = self._annotationListWidget.currentItem()
    self._annotationButtonFrame.enabled = currentItem is not None
    button = self._annotationButtonGroup.checkedButton()
    if currentItem and button:
      if self._currentAnnotationToolWidget:
        self._currentAnnotationToolWidget.resetInteraction()
      self._onAnnotationButtonClicked(button, button.checked)
    if not currentItem and not button:
      self._removeAnnotationToolWidget()

  def _fillAnnotationTable(self):
    self._annotationListWidget.clear()
    for volume in self._volumeNodes:
      try:
        seriesType = self._seriesTypes[volume]
      except KeyError:
        seriesType = SeriesTypeFactory.getSeriesType(volume)(volume)
        self._seriesTypes[volume] = seriesType
      if seriesType:
        listWidgetItem = qt.QListWidgetItem(self._annotationListWidget)
        self._annotationListWidget.addItem(listWidgetItem)
        annotationItemWidget = AnnotationItemWidget(self._finding, seriesType)
        listWidgetItem.setSizeHint(annotationItemWidget.sizeHint)
        self._annotationListWidget.setItemWidget(listWidgetItem, annotationItemWidget)
      else:
        logging.info("Could not find matching series type for volume %s" % volume.GetName())

  def _onAnnotationToolSelected(self, seriesType, mrmlNodeCLass):
    self._removeAnnotationToolWidget()
    annotation = self._finding.getOrCreateAnnotation(seriesType, mrmlNodeCLass)
    annotationWidgetClass = AnnotationWidgetFactory.getEligibleAnnotationWidgetClass(annotation.mrmlNode)
    if annotationWidgetClass:
      self._currentAnnotationToolWidget = self._getOrCreateAnnotationToolWidget(annotationWidgetClass, seriesType)

  def _getAnnotationItemWidgetForParameterNode(self, pNode):
    for idx in range(self._annotationListWidget.count):
      item = self._annotationListWidget.item(idx)
      widget = self._annotationListWidget.itemWidget(item)
      if widget.parameterNode is pNode:
        return widget
    return None

  def _onAnnotationToolDeselected(self, seriesType, mrmlNodeCLass):
    annotation = self._finding.getOrCreateAnnotation(seriesType, mrmlNodeCLass)
    if not annotation.mrmlNode:
      self._finding.deleteAnnotation(seriesType, mrmlNodeCLass)
    self._removeAnnotationToolWidget()

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