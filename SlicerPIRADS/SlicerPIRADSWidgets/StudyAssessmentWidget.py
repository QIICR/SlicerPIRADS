import qt
import os
import slicer

from .AssessmentDialog import AssessmentDialog
from SlicerDevelopmentToolboxUtils.mixins import GeneralModuleMixin


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