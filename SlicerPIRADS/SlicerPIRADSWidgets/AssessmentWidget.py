import qt
import ctk
import os
import slicer

from SlicerDevelopmentToolboxUtils.forms.FormsDialog import FormsDialog
from SlicerDevelopmentToolboxUtils.mixins import GeneralModuleMixin
from SlicerDevelopmentToolboxUtils.icons import Icons

class AssessmentWidget(ctk.ctkCollapsibleButton, GeneralModuleMixin):

  def __init__(self, forms, title, parent=None):
    ctk.ctkCollapsibleButton.__init__(self, parent)
    self._forms = forms
    self.text = title
    self.modulePath = os.path.dirname(slicer.util.modulePath("SlicerPIRADS"))
    self.setup()

  def setup(self):
    self._assessmentFormWidget = None
    self.setLayout(qt.QGridLayout())
    self._loadUI()
    self.layout().addWidget(self.ui)
    self._setupConnections()

  def _loadUI(self):
    path = os.path.join(self.modulePath, 'Resources', 'UI', 'AssessmentWidget.ui')
    self.ui = slicer.util.loadUI(path)
    self._assessmentButton = self.ui.findChild(qt.QPushButton, "assessmentButton")
    self._assessmentStatusLabel = self.ui.findChild(qt.QLabel, "assessmentStatusLabel")

  def _setupConnections(self):
    self._assessmentButton.clicked.connect(self._onAssessmentButtonClicked)
    self.destroyed.connect(self._cleanupConnections)

  def _cleanupConnections(self):
    self._assessmentButton.clicked.disconnect(self._onAssessmentButtonClicked)

  def _onAssessmentButtonClicked(self):
    # TODO: take care of situations when number of forms get changed in between
    if not self._assessmentFormWidget:
        forms = [os.path.join(self.modulePath, 'Resources', 'Forms', f) for f in self._forms.split(" ")]
        self._assessmentFormWidget = FormsDialog(forms)
    if self._assessmentFormWidget.exec_():
      self._assessmentButton.icon = Icons.edit
      self._assessmentStatusLabel.setText("Assessment done")
      self._assessmentButton.setToolTip("Modify assessment")

  def getData(self):
    try:
      return self._assessmentFormWidget.getData()
    except AttributeError:
      return {}