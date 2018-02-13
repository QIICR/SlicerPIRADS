import unittest

from SlicerPIRADSWidgets.AssessmentWidget import AssessmentLogic


__all__ = ['AssessmentLogicTest']


class AssessmentLogicTest(unittest.TestCase):

  def test_input_schema_file_names(self):
    fileNames = ["Clinical_Information.json", "Procedure_Information.json"]

    logic = AssessmentLogic(fileNames)

    self.assertListEqual(logic.schemaFiles, fileNames)