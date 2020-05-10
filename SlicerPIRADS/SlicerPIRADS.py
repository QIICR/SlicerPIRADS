import slicer
import os
import qt
import vtk
import ctk
import logging
from slicer.ScriptedLoadableModule import ScriptedLoadableModule, ScriptedLoadableModuleWidget, ScriptedLoadableModuleLogic
from collections import OrderedDict

from SlicerDevelopmentToolboxUtils.mixins import UICreationHelpers, GeneralModuleMixin, ModuleWidgetMixin
from SlicerDevelopmentToolboxUtils.icons import Icons
from SlicerDevelopmentToolboxUtils.buttons import ModuleSettingsButton, CrosshairButton
from SlicerDevelopmentToolboxUtils.helpers import WatchBoxAttribute
from SlicerDevelopmentToolboxUtils.widgets import DICOMBasedInformationWatchBox
from SlicerDevelopmentToolboxUtils.constants import DICOMTAGS

from SlicerPIRADSLogic.Configuration import SlicerPIRADSConfiguration
from SlicerPIRADSLogic.HangingProtocol import HangingProtocolFactory
from SlicerPIRADSLogic.HTMLReportCreator import HTMLReportCreator
from SlicerPIRADSLogic.SeriesType import VolumeSeriesTypeSceneObserver
from SlicerPIRADSWidgets.AssessmentWidget import AssessmentWidget
from SlicerPIRADSWidgets.DataSelectionDialog import DataSelectionDialog
from SlicerPIRADSWidgets.FindingsWidget import FindingsWidget
from SlicerPIRADSWidgets.ProstateWidget import ProstateWidget

from SlicerLayoutButtons import SlicerLayoutButtonsWidget

from qSlicerMultiVolumeExplorerModuleWidget import qSlicerMultiVolumeExplorerSimplifiedModuleWidget


class SlicerPIRADSMultiVolumeExplorer(qSlicerMultiVolumeExplorerSimplifiedModuleWidget):

  def getCurrentSeriesNumber(self):
    import string
    ref = -1
    if self._bgMultiVolumeNode:
      name = self._bgMultiVolumeNode.GetName()
      ref = string.split(name,':')[0]
    return ref

  def showInputMultiVolumeSelector(self, show):
    if show:
      self._bgMultiVolumeSelectorLabel.show()
      self.bgMultiVolumeSelector.show()
    else:
      self._bgMultiVolumeSelectorLabel.hide()
      self.bgMultiVolumeSelector.hide()

  def setMultiVolume(self, node):
    self.bgMultiVolumeSelector.setCurrentNode(node)

  def createChart(self, sliceWidget, position):
    self._multiVolumeIntensityChart.createChart(sliceWidget, position, ignoreCurrentBackground=True)

  def refreshGUIForNewBackgroundImage(self):
    self._multiVolumeIntensityChart.reset()
    self.setFramesEnabled(True)
    self.refreshFrameSlider()
    self._multiVolumeIntensityChart.bgMultiVolumeNode = self._bgMultiVolumeNode

  def onBackgroundInputChanged(self, node):
    qSlicerMultiVolumeExplorerSimplifiedModuleWidget.onBackgroundInputChanged(self)
    self.popupChartButton.setEnabled(self._bgMultiVolumeNode is not None)

  def onSliderChanged(self, frameId):
    return


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
  """ Main SlicerPIRADS module widget """

  @property
  def loadedVolumeNodes(self):
    """ Volume nodes of type or subclass slicer.vtkMRMLScalarVolumeNode that has been loaded into the mrmlScene """
    return self._loadedVolumeNodes

  @loadedVolumeNodes.setter
  def loadedVolumeNodes(self, volumes):
    self._loadedVolumeNodes = OrderedDict({volume.GetID: volume for volume in volumes})
    self.updateGUIFromData()

  def __init__(self, parent=None):
    ScriptedLoadableModuleWidget.__init__(self, parent)
    VolumeSeriesTypeSceneObserver().refresh() # is a singleton and observes the mrmlScene
    self.modulePath = os.path.dirname(slicer.util.modulePath(self.moduleName))
    SlicerPIRADSConfiguration(self.moduleName, os.path.join(self.modulePath, 'Resources', "default.cfg"))
    self._loadedVolumeNodes = OrderedDict()
    self.logic = SlicerPIRADSModuleLogic()

  def updateGUIFromData(self):
    try:
      instanceUID = list(self._loadedVolumeNodes.values())[0].GetAttribute("DICOM.instanceUIDs").split(" ")[0]
      filename = slicer.dicomDatabase.fileForInstance(instanceUID)
      self._patientWatchBox.sourceFile = filename
    except:
      self._patientWatchBox.sourceFile = None
    self._patientAssessmentWidget.enabled = len(self._loadedVolumeNodes) > 0
    self._studyAssessmentWidget.enabled = len(self._loadedVolumeNodes) > 0
    self._prostateMeasurementsWidget.enabled = len(self._loadedVolumeNodes) > 0
    self._findingsWidget.enabled = len(self._loadedVolumeNodes) > 0
    self._collapsibleMultiVolumeButton.visible = False
    self._checkForMultiVolumes()

  def exit(self):
    slicer.util.mainWindow().findChild(qt.QLabel, "LogoLabel").show()

  def enter(self):
    slicer.util.mainWindow().findChild(qt.QLabel, "LogoLabel").hide()

  def setup(self):
    """ Setup all UI elements and prepare data """
    # TODO: following line is only for the purpose of testing
    self._loadedVolumeNodes = OrderedDict({volume.GetID: volume for volume
                                           in slicer.util.getNodesByClass('vtkMRMLScalarVolumeNode')})
    ScriptedLoadableModuleWidget.setup(self)
    self._setupPatientWatchBox()
    self._setupViewSettingGroupBox()
    self._setupCollapsibleLayoutButton()
    self._patientAssessmentWidget = AssessmentWidget(forms=self.getSetting("Patient_Assessment_Forms"),
                                                   title="Patient Level Assessment")
    self._studyAssessmentWidget = AssessmentWidget(forms=self.getSetting("Study_Assessment_Forms"),
                                                   title="Study Level Assessment")
    self._prostateMeasurementsWidget = ProstateWidget()

    self._findingsWidget = FindingsWidget(maximumNumber=4)
    self._exportToHTMLButton = UICreationHelpers.createButton("Export to HTML")
    self.layout.addWidget(self._collapsibleLayoutButton)
    self._setupCollapsibleMultiVolumeExplorerButton()
    self.layout.addWidget(self._collapsibleMultiVolumeButton)
    self.layout.addWidget(self._patientAssessmentWidget)
    self.layout.addWidget(self._studyAssessmentWidget)
    self.layout.addWidget(self._prostateMeasurementsWidget)
    self.layout.addWidget(self._findingsWidget)
    self.layout.addWidget(self._exportToHTMLButton)
    self._stepButtonGroup = qt.QButtonGroup()
    self._stepButtonGroup.addButton(self._patientAssessmentWidget, 1)
    self._stepButtonGroup.addButton(self._studyAssessmentWidget, 2)
    self._stepButtonGroup.addButton(self._prostateMeasurementsWidget, 3)
    self._stepButtonGroup.addButton(self._findingsWidget, 4)
    self.layout.addStretch(1)
    self._setupConnections()
    self.updateGUIFromData()

  def _setupPatientWatchBox(self):
    WatchBoxAttribute.TRUNCATE_LENGTH = 20
    patientWatchBoxInformation = [WatchBoxAttribute('PatientName', "Patient's Name: ", DICOMTAGS.PATIENT_NAME),
                                  WatchBoxAttribute('PatientID', 'Patient ID: ', DICOMTAGS.PATIENT_ID),
                                  WatchBoxAttribute('DOB', "Patient's Birth Date: ", DICOMTAGS.PATIENT_BIRTH_DATE),
                                  WatchBoxAttribute('StudyDate', 'Study Date: ', DICOMTAGS.STUDY_DATE)]
    self._patientWatchBox = DICOMBasedInformationWatchBox(patientWatchBoxInformation, title="Patient Information",
                                                         columns=2)
    self._patientWatchBox.setStyleSheet("")
    self.layout.addWidget(self._patientWatchBox)

  def _setupViewSettingGroupBox(self):
    self._loadDataButton = UICreationHelpers.createButton("", toolTip="Load Data")
    self._loadDataButton.setIcon(Icons.open)
    self._crosshairButton = CrosshairButton()
    self._settingsButton = ModuleSettingsButton(self.moduleName)
    self._settingsButton.enabled = False
    self.layout.addWidget(UICreationHelpers.createHLayout([self._loadDataButton, self._crosshairButton,
                                                           self._settingsButton]))

  def _setupCollapsibleLayoutButton(self):
    self._collapsibleLayoutButton = ctk.ctkCollapsibleButton()
    self._collapsibleLayoutButton.text = "Layout"
    self._collapsibleLayoutButton.collapsed = 0
    self._collapsibleLayoutButton.setLayout(qt.QVBoxLayout())
    self._layoutButtonsWidget = SlicerLayoutButtonsWidget(parent=self._collapsibleLayoutButton)
    self._layoutButtonsWidget.setup()
    self._layoutButtonsWidget.hideReloadAndTestArea()
    self._layoutButtonsWidget.setDisplayForegroundOnly()

  def _setupConnections(self):
    self._loadDataButton.clicked.connect(self._onLoadButtonClicked)
    self._exportToHTMLButton.clicked.connect(self._onExportToHTMLButtonClicked)

    self._multiVolumeExplorer.frameSlider.connect('valueChanged(double)', self.onSliderChanged)

  def _onExportToHTMLButtonClicked(self):
    creator = HTMLReportCreator(self._findingsWidget.getAssessmentCalculator())
    creator.generateReport()

  def _setupCollapsibleMultiVolumeExplorerButton(self):
    self._collapsibleMultiVolumeButton = ctk.ctkCollapsibleButton()
    self._collapsibleMultiVolumeButton.text = "MultiVolumeExplorer"
    self._collapsibleMultiVolumeButton.collapsed = True
    self._collapsibleMultiVolumeButton.visible = False
    self._collapsibleMultiVolumeButton.setLayout(qt.QFormLayout())
    self._multiVolumeExplorer = SlicerPIRADSMultiVolumeExplorer(self._collapsibleMultiVolumeButton.layout())
    self._multiVolumeExplorer.setup()

  def onSliderChanged(self, newValue):
    newValue = int(newValue)
    multiVolumeNode = self._multiVolumeExplorer.getBackgroundMultiVolumeNode()
    multiVolumeNode.GetDisplayNode().SetFrameComponent(newValue)

  def _onLoadButtonClicked(self):
    self._dataSelectionDialog = DataSelectionDialog()
    self._loadedVolumeNodes = OrderedDict()

    nodeAddedObserver = slicer.mrmlScene.AddObserver(slicer.mrmlScene.NodeAddedEvent, self._onVolumeNodeAdded)
    nodeRemovedObserver = slicer.mrmlScene.AddObserver(slicer.mrmlScene.NodeRemovedEvent, self._onVolumeNodeRemoved)
    try:
      if self._dataSelectionDialog.exec_():
        self._hangingProtocol = HangingProtocolFactory.getHangingProtocol(self.loadedVolumeNodes.values())
        if not self._hangingProtocol:
          raise RuntimeError("No eligible hanging protocol found.")
        background = list(self._loadedVolumeNodes.values())[0]
        self.logic.viewerPerVolume(volumeNodes=self._loadedVolumeNodes.values(), layout=self._hangingProtocol.LAYOUT,
                                   background=background)
        ModuleWidgetMixin.linkAllSliceWidgets(1)
        for sliceWidget in ModuleWidgetMixin.getAllVisibleWidgets():
          sliceWidget.mrmlSliceNode().RotateToVolumePlane(background)
        self._checkForMultiVolumes()
    except Exception as exc:
      logging.error(exc)
    finally:
      slicer.mrmlScene.RemoveObserver(nodeAddedObserver)
      slicer.mrmlScene.RemoveObserver(nodeRemovedObserver)
      self.updateGUIFromData()

  def _checkForMultiVolumes(self):
    multiVolumes = slicer.util.getNodesByClass('vtkMRMLMultiVolumeNode')
    self._multiVolumeExplorer.showInputMultiVolumeSelector(len(multiVolumes) > 1)
    multiVolume = None
    if len(multiVolumes) == 1:
      multiVolume = multiVolumes[0]
    elif len(multiVolumes) > 1:
      multiVolume = max(multiVolumes, key=lambda mv: mv.GetNumberOfFrames)
      # TODO: set selector
    self._multiVolumeExplorer.setMultiVolume(multiVolume)
    self._showMultiVolumeExplorer(len(multiVolumes) > 0)

  def _showMultiVolumeExplorer(self, show):
    if show:
      self._collapsibleMultiVolumeButton.show()
    else:
      self._collapsibleMultiVolumeButton.hide()

  @vtk.calldata_type(vtk.VTK_OBJECT)
  def _onVolumeNodeAdded(self, caller, event, callData):
    if isinstance(callData, slicer.vtkMRMLScalarVolumeNode):
      self._loadedVolumeNodes[callData.GetID()] = callData

  @vtk.calldata_type(vtk.VTK_OBJECT)
  def _onVolumeNodeRemoved(self, caller, event, callData):
    if isinstance(callData, slicer.vtkMRMLScalarVolumeNode):
      try:
        del self._loadedVolumeNodes[callData.GetID()]
      except KeyError:
        pass


class SlicerPIRADSModuleLogic(ScriptedLoadableModuleLogic):

  def __init__(self):
    ScriptedLoadableModuleLogic.__init__(self)

  @classmethod
  def viewerPerVolume(cls, volumeNodes, layout, background, opacity=1.0):
    """ Load each volume in the scene into its own slice viewer and link them all together.
    If background is specified, put it in the background of all viewers and make the other volumes be the foreground.
    If label is specified, make it active as the label layer of all viewers. Return a map of slice nodes indexed by
    the view name (given or generated). Opacity applies only when background is selected.
    """

    if not volumeNodes:
      raise ValueError("VolumeNodes are supposed to be non empty")

    layoutManager = slicer.app.layoutManager()
    layoutManager.setLayout(layout)

    sliceWidgets = list(ModuleWidgetMixin.getAllVisibleWidgets())

    slicer.app.processEvents()

    for index, volume in enumerate(volumeNodes):
      sliceWidget = sliceWidgets[index]
      volumeNodeID = volume.GetID()

      compositeNode = sliceWidget.mrmlSliceCompositeNode()
      compositeNode.SetBackgroundVolumeID(background.GetID())
      compositeNode.SetForegroundVolumeID(volumeNodeID)
      compositeNode.SetForegroundOpacity(opacity)

      sliceNode = sliceWidget.mrmlSliceNode()
      orientation = cls.getOrientation(volume)
      if orientation:
        sliceNode.SetOrientation(orientation)
      sliceNode.RotateToVolumePlane(volume)
      sliceWidget.fitSliceToBackground()

  @classmethod
  def getOrientation(cls, volumeNode):
    name = volumeNode.GetName().lower()
    orientation = 'Axial'
    if 'sag' in name:
      orientation = 'Sagittal'
    elif 'cor' in name:
      orientation = 'Coronal'
    return orientation


class SlicerPIRADSSlicelet(qt.QWidget):
  """ SlicerPIRADSSlicelet takes complexity away so that the user can focus on their tasks with less confusion """

  def __init__(self):
    qt.QWidget.__init__(self)
    self.mainWidget = qt.QWidget()
    self.mainWidget.objectName = "qSlicerAppMainWindow"
    self.mainWidget.setLayout(qt.QHBoxLayout())

    self._setupLayoutWidget()

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
    self.splitter.splitterMoved.connect(self._onSplitterMoved)

    self.splitter.setStretchFactor(0, 0)
    self.splitter.setStretchFactor(1, 1)
    self.splitter.handle(1).installEventFilter(self)

    self.mainWidget.layout().addWidget(self.splitter)
    self.mainWidget.show()
    self._configureStyle()

  def _configureStyle(self):
    slicer.app.setStyleSheet("""
      QWidget{
        background-color: #555555;
        color: white;
      }
    """)

  def _setupLayoutWidget(self):
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
      self._onSplitterClick()

  def _onSplitterMoved(self, pos, index):
    vScroll = self.scrollArea.verticalScrollBar()
    vScrollbarWidth = 4 if not vScroll.isVisible() else vScroll.width + 4
    if self.scrollArea.minimumWidth != self.widget.parent.minimumSizeHint.width() + vScrollbarWidth:
      self.scrollArea.setMinimumWidth(self.widget.parent.minimumSizeHint.width() + vScrollbarWidth)

  def _onSplitterClick(self):
    if self.splitter.sizes()[0] > 0:
      self.splitter.setSizes([0, self.splitter.sizes()[1]])
    else:
      minimumWidth = self.widget.parent.minimumSizeHint.width()
      self.splitter.setSizes([minimumWidth, self.splitter.sizes()[1] - minimumWidth])


if __name__ == "SlicerPIRADSSlicelet":
  slicelet = SlicerPIRADSSlicelet()


import ctk
import os
import slicer
import qt
from random import random
from SlicerDevelopmentToolboxUtils.events import SlicerDevelopmentToolboxEvents as events

from SlicerDevelopmentToolboxUtils.mixins import ParameterNodeObservationMixin, GeneralModuleMixin

from SlicerPIRADSLogic.Annotation import Ruler
from SlicerPIRADSLogic.Finding import Finding
from SlicerPIRADSLogic.SeriesType import *


class ProstateWidget(ctk.ctkCollapsibleButton, GeneralModuleMixin):

  LINEAR_MEASUREMENT = "Linear Measurement"
  VOLUMETRIC_MEASUREMENT= "Volumetric Measurement"

  StartedEvent = events.StartedEvent
  FinishedEvent = events.FinishedEvent
  CanceledEvent = events.CanceledEvent

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

    for name, enabled in [(self.LINEAR_MEASUREMENT, True), (self.VOLUMETRIC_MEASUREMENT, False)]:
      action = qt.QAction(name, actionGroup)
      action.setEnabled(enabled)
      menu.addAction(action)
      actionGroup.addAction(action)
      action.triggered.connect(lambda triggered, a=action: self._onActionTriggered(a))

  def _onActionTriggered(self, action):
    action.setEnabled(False)

    if action.text == self.LINEAR_MEASUREMENT:
      logging.debug("Starting creation of linear measurement for prostate in ax, sag, and cor orientations")
      measurementCreator = LinearMeasurementCreator()
      measurementCreator.start()
      measurements = measurementCreator.getMeasurements()
    elif action.text == self.VOLUMETRIC_MEASUREMENT:
      print("create volumetric measurement")

    # TODO: disable UI and add buttons to cancel current action

    # Depending on type
    # finding = Finding("Finding %s" % random.randint(0, 10))
    # self._findingsListModel.addFinding(finding)
    # self._measurementsListWidget.selectionModel().clear()
    # model = self._measurementsListWidget.model()
    # self._measurementsListWidget.selectionModel().setCurrentIndex(model.index(model.rowCount() - 1, 0),
    #                                                               qt.QItemSelectionModel.Select)
    # self._updateButtons()

  def _setupConnections(self):
    def setupConnections(funcName="connect"):
      getattr(self._measurementsListWidget, funcName)("customContextMenuRequested(QPoint)", self._onMeasurementItemRightClicked)
      getattr(self._measurementsListWidget.selectionModel(), funcName)("currentRowChanged(QModelIndex, QModelIndex)",
                                                                       self._onFindingSelectionChanged)

    setupConnections()
    slicer.app.connect('aboutToQuit()', self.deleteLater)
    self.destroyed.connect(lambda : setupConnections(funcName="disconnect"))

  def _onMeasurementItemRightClicked(self, point):
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

  def _onAddMeasurementButtonClicked(self):
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


class LinearMeasurementCreator(ParameterNodeObservationMixin):

  ORIENTATIONS = ["Axial", "Sagittal", "Coronal"]
  DEFAULT_SERIES_TYPES = {"Axial": T2a, "Sagittal": T2s, "Coronal": T2c}
  ALTERNATIVE_SERIES_TYPE = T2a

  StartedEvent = events.StartedEvent
  FinishedEvent = events.FinishedEvent
  DataChangedEvent = events.DataChangedEvent

  def __init__(self):
    self._measurements = {orientation: None for orientation in self.ORIENTATIONS}

  def reset(self):
    for orientation, measurement in self._measurements.items():
      if measurement:
        slicer.mrmlScene.RemoveNode(measurement)
        self._measurements[orientation] = None

  def start(self, caller=None, event=None):
    # decide which seriesType to use and which orientation
    self.invokeEvent(self.StartedEvent)
    self._start()

  def _start(self, caller=None, event=None):
    for orientation in self.ORIENTATIONS:
      if not self._measurements[orientation]:
        seriesTypeClass = self.DEFAULT_SERIES_TYPES[orientation]
        volumeNode = None
        for volume, seriesType in VolumeSeriesTypeSceneObserver().volumeSeriesTypes.items():
          if isinstance(seriesType, seriesTypeClass):
            volumeNode = volume
            break
        if not volumeNode:
          logging.error("Volume with series type %s for %s measurement not found" % (seriesTypeClass.getName(),
                                                                                     orientation.lower()))
        else:
          # TODO: set orientations!
          # TODO: enable only the viewer to create annotation in
          # TODO: find volume node to use for annotating
          ruler = Ruler(volumeNode)
          self._measurements[orientation] = ruler
          ruler.addEventObserver(ruler.AnnotationFinishedEvent, self._start)
          break

    if all(value is not None for value in self._measurements.values()):
      self.invokeEvent(self.FinishedEvent)

  def getMeasurements(self):
    return self._measurements


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