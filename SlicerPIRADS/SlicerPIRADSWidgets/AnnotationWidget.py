import qt
import vtk
import ctk
import os
import slicer

from SegmentEditor import SegmentEditorWidget

from SlicerDevelopmentToolboxUtils.mixins import ParameterNodeObservationMixin, ModuleLogicMixin
from SlicerDevelopmentToolboxUtils.constants import DICOMTAGS
from SlicerDevelopmentToolboxUtils.icons import Icons


class AnnotationWidgetFactory(object):
  # TODO: write test
  # helper class for delivering widget to user with tools

  @staticmethod
  def getAnnotationWidgetForMRMLNode(mrmlNode):
    if mrmlNode.__class__.__name__ == "vtkMRMLSegmentationNode":
      return CustomSegmentEditorWidget


class AnnotationItemWidget(qt.QWidget, ParameterNodeObservationMixin):

  def __init__(self, finding, seriesType):
    super(AnnotationItemWidget, self).__init__()
    self.modulePath = os.path.dirname(slicer.util.modulePath("SlicerPIRADS"))
    self._seriesType = seriesType
    self._finding = finding
    self.setup()
    self._processData()

  def setup(self):
    self.setLayout(qt.QGridLayout())
    path = os.path.join(self.modulePath, 'Resources', 'UI', 'AnnotationItemWidget.ui')
    self.ui = slicer.util.loadUI(path)
    self.visibilityButton = self.ui.findChild(qt.QPushButton, "visibilityButton")
    self.visibilityButton.setIcon(Icons.visible_on)
    self.visibilityButton.checkable = True
    self.visibilityButton.checked = True
    self._seriesTypeLabel = self.ui.findChild(qt.QLabel, "seriesTypeLabel")
    self.layout().addWidget(self.ui)
    self._setupConnections()

  def _setupConnections(self):
    self.visibilityButton.toggled.connect(self._onVisibilityButtonToggled)
    self.destroyed.connect(self._cleanupConnections)

  def _onVisibilityButtonToggled(self, checked):
    self.visibilityButton.setIcon(Icons.visible_on if checked else Icons.visible_off)
    self._finding.setSeriesTypeVisible(self._seriesType, checked)

  def _cleanupConnections(self):
    self.visibilityButton.toggled.disconnect(self._onVisibilityButtonToggled)

  def _processData(self, caller=None, event=None):
    self._seriesTypeLabel.text = "{}: {}".format(ModuleLogicMixin.getDICOMValue(self._seriesType.getVolume(),
                                                                                DICOMTAGS.SERIES_NUMBER),
                                                 self._seriesType.getName())

  def getSeriesType(self):
    return self._seriesType


class AnnotationToolWidget(object):

  MRML_NODE_CLASS = None

  @property
  def annotation (self):
      return self._finding.getOrCreateAnnotation(self._seriesType, self.MRML_NODE_CLASS)

  def __init__(self, finding, seriesType):
    if not self.MRML_NODE_CLASS:
      raise NotImplementedError
    self._finding = finding
    self._seriesType = seriesType

  def _updateFromData(self):
    raise NotImplementedError

  def setData(self, finding, seriesType):
    self._finding = finding
    self._seriesType = seriesType
    self._updateFromData()

  def resetInteraction(self):
    raise NotImplementedError


class CustomSegmentEditorWidget(AnnotationToolWidget, SegmentEditorWidget):

  MRML_NODE_CLASS = "vtkMRMLSegmentationNode"

  def __init__(self, parent, finding, seriesType):
    AnnotationToolWidget.__init__(self, finding, seriesType)
    SegmentEditorWidget.__init__(self, parent)
    self.setup()

  def _updateFromData(self):
    self.editor.setSegmentationNode(self.annotation.mrmlNode)

  def setup(self):
    SegmentEditorWidget.setup(self)
    self.editor.setAutoShowMasterVolumeNode(False)
    if self.developerMode:
      self.reloadCollapsibleButton.hide()
    self.editor.switchToSegmentationsButtonVisible = False
    self.editor.segmentationNodeSelectorVisible = False
    self.editor.masterVolumeNodeSelectorVisible = False
    self.editor.setEffectButtonStyle(qt.Qt.ToolButtonIconOnly)
    self.editor.setEffectNameOrder(['Paint', 'Erase', 'Draw'])
    self.editor.unorderedEffectsVisible = False
    self.editor.findChild(qt.QPushButton, "AddSegmentButton").hide()
    self.editor.findChild(qt.QPushButton, "RemoveSegmentButton").hide()
    self.editor.findChild(ctk.ctkMenuButton, "Show3DButton").hide()
    self.editor.findChild(ctk.ctkExpandableWidget, "SegmentsTableResizableFrame").hide()
    self._updateFromData()

  def delete(self):
    self.editor.delete()

  def resetInteraction(self):
    self.editor.setActiveEffectByName("Selection")