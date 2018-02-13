import unittest

from SlicerPIRADSWidgets.AssessmentWidget import AssessmentWidget, AssessmentLogic

__all__ = ['AssessmentLogicTests', 'AssessmentWidgetTests']


class AssessmentWidgetTests(unittest.TestCase):

  def test_instantiation(self):
    pass

class AssessmentLogicTests(unittest.TestCase):

  def test_input_schema_file_names(self):
    fileNames = ["Clinical_Information.json", "Procedure_Information.json"]

    logic = AssessmentLogic(fileNames)

    self.assertListEqual(logic.schemaFiles, fileNames)