import qt
import logging

from SlicerPIRADSLogic.FormGeneratorFactory import FormGeneratorFactory
from SlicerDevelopmentToolboxUtils.mixins import UICreationHelpers, GeneralModuleMixin


class AssessmentWidget(qt.QDialog):

  def __init__(self, schemaFiles, parent=None):
    qt.QDialog.__init__(parent)
    # TODO: could be one file or a list
    # always assuming that a list is delivered
    self.logic = AssessmentLogic(schemaFiles)

    self.forms = []
    self.setup()
    self.setupConnections()

  def setup(self):
    self.setLayout(qt.QGridLayout)
    #TODO: if list of schema, then create navigation buttons

  def setupConnections(self):
    pass


class AssessmentLogic(object):

  @property
  def schemasFiles(self):
    return self._schemaFiles

  @schemasFiles.setter
  def schemaFiles(self, schemaFiles):
    if type(schemaFiles) is list:
      assert all(type(s) is str for s in schemaFiles), ""
    elif type(schemaFiles) is str:
      schemaFiles = [schemaFiles]
    else:
      raise ValueError("Value %s is not valid for schema files. It has to be either a list or a string" % schemaFiles)
    self._schemaFiles = schemaFiles

  def __init__(self, schemaFiles):
    self.schemaFiles = schemaFiles