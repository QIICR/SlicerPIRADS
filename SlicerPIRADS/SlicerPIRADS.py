import slicer
import os
import qt
import vtk
import logging
from slicer.ScriptedLoadableModule import *

from SlicerDevelopmentToolboxUtils.mixins import UICreationHelpers, GeneralModuleMixin, ParameterNodeObservationMixin
from SlicerDevelopmentToolboxUtils.mixins import ModuleWidgetMixin

from SlicerPIRADSLogic.Configuration import SlicerPIRADSConfiguration
from SlicerPIRADSLogic.HangingProtocol import HangingProtocolFactory
from SlicerPIRADSWidgets.StudyAssessmentWidget import StudyAssessmentWidget
from SlicerPIRADSWidgets.DataSelectionDialog import DataSelectionDialog
from SlicerPIRADSWidgets.FindingsWidget import FindingsWidget


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
    self._findingsWidget = FindingsWidget()
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
        sliceNode = logic.GetSliceNode()
        sliceNode.SetOrientationToAxial()
        sliceNode.RotateToVolumePlane(volume)
      except IndexError:
        break


class SlicerPIRADSLogic(ScriptedLoadableModuleLogic):

  def __init__(self):
    ScriptedLoadableModuleLogic.__init__(self)


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