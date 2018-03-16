import slicer
import os
import qt
import vtk
import ctk
import logging
from slicer.ScriptedLoadableModule import *

from SlicerDevelopmentToolboxUtils.mixins import UICreationHelpers, GeneralModuleMixin, ParameterNodeObservationMixin
from SlicerDevelopmentToolboxUtils.mixins import ModuleWidgetMixin, ModuleLogicMixin
from SlicerDevelopmentToolboxUtils.decorators import logmethod
from SlicerPIRADSLogic.Configuration import SlicerPIRADSConfiguration
from SlicerPIRADSWidgets.AssessmentDialog import AssessmentDialog
from SlicerPIRADSWidgets.DataSelectionDialog import DataSelectionDialog
from SegmentEditor import SegmentEditorWidget


class SlicerPIRADS(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "Slicer PIRADS"
    self.parent.categories = ["Informatics", "Quantification", "Segmentation"]
    self.parent.dependencies = ["SlicerDevelopmentToolbox"]
    self.parent.contributors = ["Christian Herz (SPL, BWH)", "Andrey Fedorov (SPL, BWH)"]
    self.parent.helpText = """
      
    """
    self.parent.acknowledgementText = """ 
      Surgical Planning Laboratory, Brigham and Women's Hospital, Harvard 
      Medical School, Boston, USA This work was supported in part by the 
      National Institutes of Health through grants U24 CA180918,
      R01 CA111288 and P41 EB015898.
    """


class SlicerPIRADSWidget(ScriptedLoadableModuleWidget, GeneralModuleMixin):

  def __init__(self, parent=None):
    ScriptedLoadableModuleWidget.__init__(self, parent)
    self.modulePath = os.path.dirname(slicer.util.modulePath(self.moduleName))
    SlicerPIRADSConfiguration(self.moduleName, os.path.join(self.modulePath, 'Resources', "default.cfg"))
    self._loadedVolumeNodes = []

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)
    self._loadDataButton = UICreationHelpers.createButton("Load Data")
    self._studyAssessmentWidget = StudyAssessmentWidget()
    self._findingsWidget = SlicerPIRADSSFindingsWidget()
    self.layout.addWidget(self._loadDataButton)
    self.layout.addWidget(self._studyAssessmentWidget)
    self.layout.addWidget(self._findingsWidget)
    self.layout.addStretch(1)
    self._setupConnections()

  def _setupConnections(self):
    self._loadDataButton.clicked.connect(self._onLoadButtonClicked)

  def _onLoadButtonClicked(self):
    self._dataSelectionDialog = DataSelectionDialog()
    self._loadedVolumeNodes = []

    sceneObserver = slicer.mrmlScene.AddObserver(slicer.mrmlScene.NodeAddedEvent, self._onVolumeNodeAdded)
    try:
      if self._dataSelectionDialog.exec_():
        self._hangingProtocol = HangingProtocolFactory.getHangingProtocol(self._loadedVolumeNodes)
        if self._hangingProtocol:
          slicer.app.layoutManager().setLayout(self._hangingProtocol.LAYOUT)
          self._organizeVolumesIntoViews()
    except Exception as exc:
      logging.error(exc.message)
    finally:
      slicer.mrmlScene.RemoveObserver(sceneObserver)

  @vtk.calldata_type(vtk.VTK_OBJECT)
  def _onVolumeNodeAdded(self, caller, event, callData):
    if isinstance(callData, slicer.vtkMRMLScalarVolumeNode):
      self._loadedVolumeNodes.append(callData)

  def _organizeVolumesIntoViews(self):
    widgets = list(ModuleWidgetMixin.getAllVisibleWidgets())
    assert len(widgets) >= len(self._loadedVolumeNodes)
    for idx, widget in enumerate(widgets):
      try:
        volume = self._loadedVolumeNodes[idx]
        widget.mrmlSliceCompositeNode().SetBackgroundVolumeID(volume.GetID())
        logic = widget.sliceLogic()
        logic.FitSliceToAll()
        logic.GetSliceNode().SetOrientationToAxial()
      except IndexError:
        break



class SlicerPIRADSLogic(ScriptedLoadableModuleLogic):

  def __init__(self):
    ScriptedLoadableModuleLogic.__init__(self)


class StudyAssessmentWidget(qt.QWidget, GeneralModuleMixin):

  def __init__(self, parent=None):
    qt.QWidget.__init__(self, parent)
    self.modulePath = os.path.dirname(slicer.util.modulePath("SlicerPIRADS"))
    self.setup()

  def setup(self):
    self._assessmentFormWidget = None

    self.setLayout(qt.QGridLayout())
    self._loadUI()
    self.layout().addWidget(self.ui)
    self._setupConnections()

  def _loadUI(self):
    path = os.path.join(self.modulePath, 'Resources', 'UI', 'StudyLevelAssessmentWidget.ui')
    self.ui = slicer.util.loadUI(path)
    self._studyLevelAssessmentButton = self.ui.findChild(qt.QPushButton, "studyLevelAssessmentButton")
    self._studyAssessmentListView = self.ui.findChild(qt.QListView, "studyAssessmentView")

  def _setupConnections(self):
    self._studyLevelAssessmentButton.clicked.connect(self._onStudyAssessmentButtonClicked)
    self.destroyed.connect(self._cleanupConnections)

  def _cleanupConnections(self):
    self._studyLevelAssessmentButton.clicked.disconnect(self._onStudyAssessmentButtonClicked)

  def _onStudyAssessmentButtonClicked(self):
    if self._studyAssessmentListView.count != 0:
      self._studyAssessmentListView.clear()
      self._studyLevelAssessmentButton.icon = qt.QIcon(":/Icons/Add.png")
    else:
      # TODO: take care of situations when number of forms get changed in between
      if not self._assessmentFormWidget:
        forms = GeneralModuleMixin.getSetting(self, "Study_Assessment_Forms", moduleName="SlicerPIRADS")
        if forms:
          forms = [os.path.join(self.modulePath, 'Resources', 'Forms', f) for f in forms.split(" ")]
          self._assessmentFormWidget = AssessmentDialog(forms)
      self._assessmentFormWidget.exec_()
      print self._assessmentFormWidget.getData()
      # TODO: if item added, change icon and react
      self._studyAssessmentListView.addItem(self._assessmentFormWidget.getData())
      self._studyLevelAssessmentButton.icon = qt.QIcon(":/Icons/Remove.png")


class SlicerPIRADSSFindingsWidget(qt.QWidget, GeneralModuleMixin):

  def __init__(self, parent=None):
    qt.QWidget.__init__(self, parent)
    self.modulePath = os.path.dirname(slicer.util.modulePath("SlicerPIRADS"))
    self.setup()

  def setup(self):
    self._assessmentFormWidget = None
    self._currentMeasurementWidget = None

    self.setLayout(qt.QGridLayout())
    self._loadUI()
    self.layout().addWidget(self.ui)
    self._setupConnections()

  def _loadUI(self):
    path = os.path.join(self.modulePath, 'Resources', 'UI', 'FindingsWidget.ui')
    self.ui = slicer.util.loadUI(path)
    self._addFindingsButton = self.ui.findChild(qt.QPushButton, "addFindingsButton")
    self._removeFindingsButton = self.ui.findChild(qt.QPushButton, "removeFindingsButton")
    self._findingsListWidget = self.ui.findChild(qt.QListWidget, "findingsListWidget")
    self._measurementWidgetFrame = self.ui.findChild(qt.QFrame, "measurementWidgetFrame")
    self._measurementWidgetFrame.setLayout(qt.QGridLayout())
    self._updateButtons()

  def _setupConnections(self):
    self._addFindingsButton.clicked.connect(self._onAddFindingsButtonClicked)
    self._removeFindingsButton.clicked.connect(self._onRemoveFindingRequested)
    self._findingsListWidget.connect("customContextMenuRequested(QPoint)", self._onFindingItemRightClicked)
    self._findingsListWidget.itemSelectionChanged.connect(self._onSelectionChanged)
    self.destroyed.connect(self._cleanupConnections)

  def _cleanupConnections(self):
    self._addFindingsButton.clicked.disconnect(self._onAddFindingsButtonClicked)
    self._removeFindingsButton.clicked.disconnect(self._onRemoveFindingRequested)
    self._findingsListWidget.disconnect("customContextMenuRequested(QPoint)", self._onFindingItemRightClicked)
    self._findingsListWidget.itemSelectionChanged.disconnect(self._onSelectionChanged)

  def _onFindingItemRightClicked(self, point):
    if not self._findingsListWidget.currentItem():
      return
    self.listMenu = qt.QMenu()
    menu_item = self.listMenu.addAction("Remove Item")
    menu_item.triggered.connect(self._onRemoveFindingRequested)
    parentPosition = self._findingsListWidget.mapToGlobal(qt.QPoint(0, 0))
    self.listMenu.move(parentPosition + point)
    self.listMenu.show()

  def _onRemoveFindingRequested(self):
    currentItem = self._findingsListWidget.currentItem()
    widget = self._findingsListWidget.itemWidget(currentItem)
    if slicer.util.confirmYesNoDisplay("Finding '{}' is about to be deleted. Do you want to proceed?".format(widget.getFinding().getName())):
      self._findingsListWidget.model().removeRow(self._findingsListWidget.row(currentItem))
      self._updateButtons()

  def _onAddFindingsButtonClicked(self):
    # TODO: findings assessment
    measurementSelector = MeasurementToolSelectionDialog()
    if measurementSelector.exec_():
      import random
      finding = Finding()
      finding.createLesion("Finding %s" %random.randint(0,10), measurementSelector.getSelectedMRMLNodeClass())

      listWidgetItem = qt.QListWidgetItem(self._findingsListWidget)
      self._findingsListWidget.addItem(listWidgetItem)
      findingsItemWidget = FindingItemWidget(finding)
      listWidgetItem.setSizeHint(findingsItemWidget.sizeHint)
      self._findingsListWidget.setItemWidget(listWidgetItem, findingsItemWidget)

      self._findingsListWidget.selectionModel().clear()
      model = self._findingsListWidget.model()
      self._findingsListWidget.selectionModel().setCurrentIndex(model.index(model.rowCount()-1, 0),
                                                                qt.QItemSelectionModel.Select)

      self._updateButtons()

  def _onSelectionChanged(self):
    # TODO: jump to centroid of lesion
    self._updateButtons()
    self._deleteCurrentToolFrameWidget()
    self._displayMeasurementToolForSelectedFinding()

  def _displayMeasurementToolForSelectedFinding(self):
    currentItem = self._findingsListWidget.currentItem()
    if currentItem:
      widget = self._findingsListWidget.itemWidget(currentItem)
      finding = widget.getFinding()
      self._currentMeasurementWidget = \
        MeasurementWidgetFactory.getMeasurementWidgetForMRMLNode(finding.getLesion().mrmlNode)(parent=self._measurementWidgetFrame,
                                                                                               finding=finding)

  def _deleteCurrentToolFrameWidget(self):
    if self._currentMeasurementWidget:
      self._currentMeasurementWidget.delete()

  def _updateButtons(self):
    self._removeFindingsButton.setEnabled(self._findingsListWidget.selectedIndexes())


class FindingItemWidget(qt.QWidget):

  def __init__(self, finding):
    super(FindingItemWidget, self).__init__()
    self.modulePath = os.path.dirname(slicer.util.modulePath("SlicerPIRADS"))
    self._finding = finding
    self._finding.addEventObserver(self._finding.DataChangedEvent, self._processData)
    self.setup()
    self._processData()

  def getFinding(self):
    return self._finding

  def setup(self):
    self.setLayout(qt.QGridLayout())
    path = os.path.join(self.modulePath, 'Resources', 'UI', 'FindingItemWidget.ui')
    self.ui = slicer.util.loadUI(path)

    self._measurementTypeLabel = self.ui.findChild(qt.QLabel, "measurementTypeLabel")
    self._findingNameLabel = self.ui.findChild(qt.QLabel, "findingNameLabel")
    self._sectorsLabel = self.ui.findChild(qt.QLabel, "sectorsLabel")
    self._measurementLabel = self.ui.findChild(qt.QLabel, "measurementLabel")
    self._prostateMapButton = self.ui.findChild(qt.QPushButton, "prostateMapButton")
    self._prostateMapDialog = None
    self.layout().addWidget(self.ui)
    self.setupConnections()

  def setupConnections(self):
    self._prostateMapButton.clicked.connect(self._onProstateMapButtonClicked)
    self.destroyed.connect(self._cleanupConnections)

  def _cleanupConnections(self):
    self._prostateMapButton.clicked.disconnect(self._onProstateMapButtonClicked)

  def _onProstateMapButtonClicked(self):
    if not self._prostateMapDialog:
      self._prostateMapDialog = ProstateSectorMapDialog()

    self._prostateMapDialog.setSelectedSectors(self._finding.getSectors())

    if self._prostateMapDialog.exec_():
      self._finding.setSectors(self._prostateMapDialog.getSelectedSectors())

  def _processData(self, caller=None, event=None):
    icon = self._finding.getIcon()
    self._measurementTypeLabel.setPixmap(icon.pixmap(qt.QSize(32, 32)))

    self._findingNameLabel.text = self._finding.getName()
    self._sectorsLabel.text = ",".join(self._finding.getSectors())
    self._measurementLabel.text = str(self._finding.getMeasurementValue())

    self._prostateMapButton.setIconSize(qt.QSize(20, 32))
    self._prostateMapButton.setIcon(qt.QIcon(os.path.join(self.modulePath, 'Resources', 'Icons', 'ProstateMap.png')))


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
    self._backgroundLabel.setPixmap(icon.pixmap(qt.QSize(622, 850)))
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


class Finding(ParameterNodeObservationMixin):

  DataChangedEvent = vtk.vtkCommand.UserEvent + 201

  def __init__(self):
    self._assessment = None
    self._lesion = None
    self._sectors = []

  @logmethod(logging.INFO)
  def __del__(self):
    if self._lesion:
      self._lesion.delete()

  def createLesion(self, name, mrmlNodeClass):
    self._lesion = LesionFactory.getLesionClassForMRMLNodeClass(mrmlNodeClass)(name)
    self._lesion.addEventObserver(self._lesion.DataChangedEvent, self.onLesionDataChanged)

  def getLesion(self):
    return self._lesion

  def getName(self):
    return self._lesion.getName()

  def setName(self, name):
    self._lesion.setName(name)

  def getIcon(self):
    if self._lesion:
      return self._lesion.getIcon()
    return None

  def getSectors(self):
    return self._sectors

  def setSectors(self, sectors):
    self._sectors = sectors
    self.invokeEvent(self.DataChangedEvent)

  def getMeasurementValue(self):
    return self._lesion.getMeasurement()

  def onLesionDataChanged(self, caller, event):
    self.invokeEvent(self.DataChangedEvent)


class LesionFactory(object):

  @staticmethod
  def getLesionClassForMRMLNodeClass(mrmlNodeClass):
    if mrmlNodeClass == "vtkMRMLSegmentationNode":
      return SegmentationLesion
    return None


class LesionBase(ParameterNodeObservationMixin):

  DataChangedEvent = vtk.vtkCommand.UserEvent + 201
  MRML_NODE_CLASS = None

  def __init__(self, name):
    if not self.MRML_NODE_CLASS:
      raise ValueError("MRML_NODE_CLASS needs to be defined for all inheriting classes of {}".format(self.__class__.__name__))
    self._name = name
    self.mrmlNode = slicer.mrmlScene.AddNewNodeByClass(self.MRML_NODE_CLASS)
    self._icon = MeasurementToolSelectionDialog.getIconFromMRMLNodeClass(self.MRML_NODE_CLASS)

  @logmethod(logging.INFO)
  def delete(self):
    if self.mrmlNode:
      slicer.mrmlScene.RemoveNode(self.mrmlNode)

  def getIcon(self):
    return self._icon

  def getMeasurement(self):
    raise NotImplementedError

  def getName(self):
    raise NotImplementedError

  def setName(self, name):
    raise NotImplementedError


class SegmentationLesion(LesionBase):

  MRML_NODE_CLASS = "vtkMRMLSegmentationNode"

  def __init__(self, name):
    super(SegmentationLesion, self).__init__(name)
    self._createAndObserveSegment()

  def _createAndObserveSegment(self):
    import vtkSegmentationCorePython as vtkSegmentationCore
    segment = vtkSegmentationCore.vtkSegment()
    segment.SetName(self._name)
    self.mrmlNode.GetSegmentation().AddSegment(segment)
    self.mrmlNode.AddObserver(vtkSegmentationCore.vtkSegmentation.SegmentModified, self._onSegmentModified)

  def getMeasurement(self):
    return 0.0

  def setName(self, name):
    return self.mrmlNode.GetSegmentation().GetNthSegment(0).SetName(name)

  def getName(self):
    return self.mrmlNode.GetSegmentation().GetNthSegment(0).GetName()

  def _onSegmentModified(self, caller, event):
    self.invokeEvent(self.DataChangedEvent)


class MeasurementToolSelectionDialog(object):

  ICON_MAP = {"vtkMRMLSegmentationNode": "SegmentEditor.png",
              "vtkMRMLAnnotationRulerNode": "Ruler.png",
              "vtkMRMLAnnotationRulerNode": "Fiducials.png"}

  def __init__(self):
    self.modulePath = os.path.dirname(slicer.util.modulePath("SlicerPIRADS"))
    self._selectedMRMLNodeClass = None
    self.setup()

  def setup(self):
    path = os.path.join(self.modulePath, 'Resources', 'UI', 'MeasurementToolSelectionDialog.ui')
    self.ui = slicer.util.loadUI(path)

    for bName in ["segmentationButton", "rulerButton", "fiducialButton"]:
      button = self.ui.findChild(qt.QPushButton, bName)
      button.setIcon(self.getIconFromMRMLNodeClass(button.property("MRML_NODE_CLASS")))
      self._connectButton(button)

  def _connectButton(self, button):
    button.clicked.connect(lambda: setattr(self, "_selectedMRMLNodeClass", button.property("MRML_NODE_CLASS")))

  def exec_(self):
    return self.ui.exec_()

  @staticmethod
  def getIconFromMRMLNodeClass(name):
    modulePath = os.path.dirname(slicer.util.modulePath("SlicerPIRADS"))
    return qt.QIcon(os.path.join(modulePath, 'Resources', 'Icons', MeasurementToolSelectionDialog.ICON_MAP[name]))

  @staticmethod
  def getIconFromMRMLNode(mrmlNode):
    return MeasurementToolSelectionDialog.getIconFromMRMLNodeClass(mrmlNode.__class__.__name__)

  def getSelectedMRMLNodeClass(self):
    return self._selectedMRMLNodeClass


class MeasurementWidgetFactory(object):
  # TODO: write test
  # helper class for delivering widget to user with tools

  @staticmethod
  def getMeasurementWidgetForMRMLNode(mrmlNode):
    if mrmlNode.__class__.__name__ == "vtkMRMLSegmentationNode":
      return SegmentEditorMeasurementWidget


class SegmentEditorMeasurementWidget(SegmentEditorWidget):

  def __init__(self, parent, finding):
    super(SegmentEditorMeasurementWidget, self).__init__(parent)
    self.parameterSetNode = None
    self.setup()
    self._finding = finding
    lesion = finding.getLesion()
    self.editor.setSegmentationNode(lesion.mrmlNode)

  def setup(self):
    super(SegmentEditorMeasurementWidget, self).setup()
    if self.developerMode:
      self.reloadCollapsibleButton.hide()
    self.editor.switchToSegmentationsButtonVisible = False
    self.editor.segmentationNodeSelectorVisible = False
    self.editor.setEffectButtonStyle(qt.Qt.ToolButtonIconOnly)
    self.editor.findChild(qt.QPushButton, "AddSegmentButton").hide()
    self.editor.findChild(qt.QPushButton, "RemoveSegmentButton").hide()
    self.editor.findChild(ctk.ctkMenuButton, "Show3DButton").hide()
    self.editor.findChild(ctk.ctkExpandableWidget, "SegmentsTableResizableFrame").hide()

  def delete(self):
    self.editor.delete()


class LesionAssessment(object):

  def __init__(self):
    self._location = None
    self._score = None

  def getLocation(self):
    return self._location

  def getScore(self):
    return self._score


class SlicerPIRADSSlicelet(qt.QWidget):

  def __init__(self):
    qt.QWidget.__init__(self)
    self.mainWidget = qt.QWidget()
    self.mainWidget.objectName = "qSlicerAppMainWindow"
    self.mainWidget.setLayout(qt.QHBoxLayout())

    self.setupLayoutWidget()

    self.moduleFrame = qt.QWidget()
    self.moduleFrame.setLayout(qt.QVBoxLayout())
    self.widget = SlicerPIRADSWidget(self.moduleFrame)
    self.widget.setup()

    self.scrollArea = qt.QScrollArea()
    self.scrollArea.setWidget(self.widget.parent)
    self.scrollArea.setWidgetResizable(True)
    self.scrollArea.setMinimumWidth(self.widget.parent.minimumSizeHint.width())

    self.splitter = qt.QSplitter()
    self.splitter.setOrientation(qt.Qt.Horizontal)
    self.splitter.addWidget(self.scrollArea)
    self.splitter.addWidget(self.layoutWidget)
    self.splitter.splitterMoved.connect(self.onSplitterMoved)

    self.splitter.setStretchFactor(0, 0)
    self.splitter.setStretchFactor(1, 1)
    self.splitter.handle(1).installEventFilter(self)

    self.mainWidget.layout().addWidget(self.splitter)
    self.mainWidget.show()
    self.configureStyle()

  def configureStyle(self):
    slicer.app.setStyleSheet("""
      QWidget{
        background-color: #555555;
        color: white;
      }
    """)

  def setupLayoutWidget(self):
    # TODO: configurable ...
    self.layoutWidget = qt.QWidget()
    self.layoutWidget.setLayout(qt.QHBoxLayout())
    layoutWidget = slicer.qMRMLLayoutWidget()
    layoutManager = slicer.qSlicerLayoutManager()
    layoutManager.setMRMLScene(slicer.mrmlScene)
    layoutManager.setScriptedDisplayableManagerDirectory(slicer.app.slicerHome + "/bin/Python/mrmlDisplayableManager")
    layoutWidget.setLayoutManager(layoutManager)
    slicer.app.setLayoutManager(layoutManager)
    layoutWidget.setLayout(slicer.vtkMRMLLayoutNode.SlicerLayoutFourUpView)
    self.layoutWidget.layout().addWidget(layoutWidget)

  def eventFilter(self, obj, event):
    if event.type() == qt.QEvent.MouseButtonDblClick:
      self.onSplitterClick()

  def onSplitterMoved(self, pos, index):
    vScroll = self.scrollArea.verticalScrollBar()
    vScrollbarWidth = 4 if not vScroll.isVisible() else vScroll.width + 4
    if self.scrollArea.minimumWidth != self.widget.parent.minimumSizeHint.width() + vScrollbarWidth:
      self.scrollArea.setMinimumWidth(self.widget.parent.minimumSizeHint.width() + vScrollbarWidth)

  def onSplitterClick(self):
    if self.splitter.sizes()[0] > 0:
      self.splitter.setSizes([0, self.splitter.sizes()[1]])
    else:
      minimumWidth = self.widget.parent.minimumSizeHint.width()
      self.splitter.setSizes([minimumWidth, self.splitter.sizes()[1] - minimumWidth])


if __name__ == "SlicerPIRADSSlicelet":
  slicelet = SlicerPIRADSSlicelet()


class HangingProtocolFactory(object):

  @staticmethod
  def getHangingProtocol(volumeNodes):
    if len(volumeNodes) == 4:
      return PIRADSHangingProtocolP1
    elif len(volumeNodes) == 6:
      return PIRADSHangingProtocolP2
    else:
      return PIRADSHangingProtocolP3


from abc import abstractmethod, ABCMeta

class HangingProtocol(object):

  __metaclass__ = ABCMeta

  SERIES_TYPES = None
  LAYOUT = None

  def __init__(self, volumeNodes):
    if not self.SERIES_TYPES or not self.LAYOUT:
      raise NotImplementedError
    self._volumeNodes = volumeNodes

  def canHandle(self, seriesTypes):
    pass


class PIRADSHangingProtocolP1(HangingProtocol):

  SERIES_TYPES = ["T2", "ADC", "DWI-b", "SUB"]
  LAYOUT = slicer.vtkMRMLLayoutNode.SlicerLayoutTwoOverTwoView


class PIRADSHangingProtocolP2(HangingProtocol):

  SERIES_TYPES = ["T2 ax", "T2 sag", "T2 cor", "ADC", "DWI-b", "SUB"]
  LAYOUT = slicer.vtkMRMLLayoutNode.SlicerLayoutThreeOverThreeView


class PIRADSHangingProtocolP3(HangingProtocol):

  SERIES_TYPES = ["T2 ax", "T2 sag", "T2 cor", "ADC", "DWI-b", "SUB", "DCE dynamic", "curve"]
  LAYOUT = slicer.vtkMRMLLayoutNode.SlicerLayoutThreeByThreeSliceView
