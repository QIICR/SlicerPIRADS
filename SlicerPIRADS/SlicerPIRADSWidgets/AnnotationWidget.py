import qt
import ctk
import os
import vtk
import slicer

from SegmentEditor import SegmentEditorWidget

from SlicerDevelopmentToolboxUtils.mixins import ParameterNodeObservationMixin, ModuleLogicMixin
from SlicerDevelopmentToolboxUtils.constants import DICOMTAGS
from SlicerDevelopmentToolboxUtils.icons import Icons


class AnnotationItemWidget(qt.QWidget, ParameterNodeObservationMixin):
  """ The AnnotationItemWidget provides functionality for displaying annotation specific information

    Displayed information include series number and series type. Additionally the user can control visibility of the
    annotation.

    Params:
      finding(Finding): finding instance that the annotation will be created for
      seriesType(SeriesType): seriesType that the annotation will be created for
      parent(qt.QWidget, optional): parent widget
  """

  def __init__(self, finding, seriesType, parent=None):
    qt.QWidget.__init__(self, parent)
    self.modulePath = os.path.dirname(slicer.util.modulePath("SlicerPIRADS"))
    self._seriesType = seriesType
    self._finding = finding
    self._finding.addEventObserver(finding.SectorSelectionChangedEvent, self._onFindingSectorSelectionChanged)
    self._finding.addEventObserver(finding.AssessmentScoreChanged, self._onFindingAssessmentScoreChanged)
    self.setup()
    self._processData()

  def setup(self):
    self.setLayout(qt.QGridLayout())
    path = os.path.join(self.modulePath, 'Resources', 'UI', 'AnnotationItemWidget.ui')
    self.ui = slicer.util.loadUI(path)
    self._visibilityButton = self.ui.findChild(qt.QPushButton, "visibilityButton")
    self._pickList = self.ui.findChild(qt.QComboBox, "picklist")
    self._onFindingSectorSelectionChanged()
    self._visibilityButton.setIcon(Icons.visible_on)
    self._visibilityButton.checkable = True
    self._visibilityButton.checked = True
    self._seriesTypeLabel = self.ui.findChild(qt.QLabel, "seriesTypeLabel")
    self.layout().addWidget(self.ui)
    self._setupConnections()

  def _setupConnections(self):
    self._visibilityButton.toggled.connect(self._onVisibilityButtonToggled)
    self._pickList.currentTextChanged.connect(self._onScoreSelectionChanged)
    self.destroyed.connect(self._cleanupConnections)

  def _onVisibilityButtonToggled(self, checked):
    self._visibilityButton.setIcon(Icons.visible_on if checked else Icons.visible_off)
    self._finding.setSeriesTypeVisible(self._seriesType, checked)

  def _cleanupConnections(self, obj):
    self._visibilityButton.toggled.disconnect()
    self._pickList.currentTextChanged.disconnect()
    self._finding.removeEventObserver(self._finding.SectorSelectionChangedEvent, self._onFindingSectorSelectionChanged)
    self._finding.removeEventObserver(self._finding.AssessmentScoreChanged, self._onFindingAssessmentScoreChanged)

  def _processData(self, caller=None, event=None):
    self._seriesTypeLabel.text = "{}: {}".format(ModuleLogicMixin.getDICOMValue(self._seriesType.getVolume(),
                                                                                DICOMTAGS.SERIES_NUMBER),
                                                 self._seriesType.getName())

  def _onFindingSectorSelectionChanged(self, caller=None, event=None):
    # TODO: Note that according to PI-RADS, there is preferred sequence for measuring lesions, depending on the lesion
    # location, but the reader can override the suggested sequence
    self._pickList.blockSignals(True)
    self._pickList.clear()
    self._pickList.addItems([" "]+ self._finding.getPickList(self._seriesType))
    self._pickList.setToolTip(self._finding.getPickListTooltip(self._seriesType))
    score = self._finding.getScore(self._seriesType)
    if score:
      index = self._pickList.findText(score)
      if index != -1:
        self._pickList.setCurrentIndex(index)
      else:
        # remove score if it couldn't be found
        self._finding.removeScore(self._seriesType)
    self._onFindingAssessmentScoreChanged()
    self._pickList.blockSignals(False)

  def _onScoreSelectionChanged(self, score):
    if score == " ":
      self._finding.removeScore(self._seriesType)
    else:
      self._finding.setScore(self._seriesType, score)

  def _onFindingAssessmentScoreChanged(self, caller=None, event=None):
    assessedSeriesTypes = self._finding.getAssessmentScores().keys()
    enabled = self._pickList.count > 1
    if enabled and self._seriesType in assessedSeriesTypes:
      enabled = True
    elif any(isinstance(self._seriesType, a.__class__.__bases__[0]) for a in assessedSeriesTypes):
      enabled = False
    self.enableScoring(enabled)

  def enableScoring(self, enable):
    self._pickList.visible = enable

  def getSeriesType(self):
    """ This method returns the series type that was assigned to this widget

      Returns:
        seriesType(SeriesType): seriesType
    """
    return self._seriesType


class AnnotationToolWidget:
  """ AnnotationToolWidget is a base class that can be used to create widgets that support a certain mrml node class

    Params:
      finding(Finding): finding instance that the annotation will be created for
      seriesType(SeriesType): seriesType that the annotation will be created for
  """

  MRML_NODE_CLASS = None
  """ MRML node class that is supported by this widget"""

  @property
  def annotation(self):
    """ Retrieves or creates the annotation that was assigned to the finding"""
    return self._finding.getOrCreateAnnotation(self._seriesType, self.MRML_NODE_CLASS)

  def __init__(self, finding, seriesType):
    if not self.MRML_NODE_CLASS:
      raise NotImplementedError
    self._finding = finding
    self._seriesType = seriesType

  def _updateFromData(self):
    raise NotImplementedError

  def setData(self, finding, seriesType):
    """ Sets finding and series type for an already existing widget to prevent reinitialization

     Params:
      finding(Finding): finding instance that the annotation will be created for
      seriesType(SeriesType): seriesType instance that the annotation will be created for
    """
    self._finding = finding
    self._seriesType = seriesType
    self._updateFromData()

  def resetInteraction(self):
    """ Resets the interaction. This can be very helpful if the user decides to cancel current action."""
    raise NotImplementedError


class CustomSegmentEditorWidget(AnnotationToolWidget, SegmentEditorWidget):
  """ CustomSegmentEditorWidget is a subclass of Slicer SegmentEditor displaying only most important UI components

    Params:
      parent(qt.QWidget): parent widget of the custom SegmentEditor
      finding(Finding): finding instance that the segmentation will be created for
      seriesType(SeriesType): seriesType that the segmentation will be created for
  """

  MRML_NODE_CLASS = "vtkMRMLSegmentationNode"

  def __init__(self, parent, finding, seriesType):
    AnnotationToolWidget.__init__(self, finding, seriesType)
    SegmentEditorWidget.__init__(self, parent)
    self.setup()

  def setupDeveloperSection(self):
    return

  def resourcePath(self, filename):
    scriptedModulesPath = os.path.dirname(slicer.util.modulePath("CustomSegmentEditorWidget"))
    return os.path.join(scriptedModulesPath, 'Resources', filename)

  def _updateFromData(self):
    self.editor.setSegmentationNode(self.annotation.mrmlNode)

  def setup(self):
    SegmentEditorWidget.setup(self)
    self.editor.setAutoShowMasterVolumeNode(False)
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


class AnnotationWidgetFactory(object):
  """ AnnotationWidgetFactory can be used to retrieve a widget providing a user interface for annotation creation.

    NOTE: Not all mrmlNodes are provided with a tool widget
  """

  SUPPORTED_MRML_NODE_WIDGETS = [CustomSegmentEditorWidget]
  """ All supported MRML node class that provide a user interface """

  @staticmethod
  def getEligibleAnnotationWidgetClass(mrmlNode):
    """ Returns one of the registered Annotation subclasses if mrmlNodeClass can be handled by one otherwise None

      Params:
        mrmlNodeClass(slicer.vtkMRMLNode): mrmlNode class to be checked for eligible annotation tool widget

      Returns:
        widget(qt.QWidget): widget if eligible class was found, otherwise None
    """
    for mrmlNodeWidgetClass in AnnotationWidgetFactory.SUPPORTED_MRML_NODE_WIDGETS:
      if mrmlNode.__class__.__name__ == mrmlNodeWidgetClass.MRML_NODE_CLASS:
        return mrmlNodeWidgetClass
    return None