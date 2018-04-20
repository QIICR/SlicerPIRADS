import unittest
import logging
import inspect
import qt

from SlicerPIRADSLogic.FormGeneratorFactory import FormGeneratorFactory
from SlicerPIRADSLogic.JSONFormGenerator import JSONStringField, JSONEnumField, JSONIntegerField


class JSONFormGeneratorTests(unittest.TestCase):

  def test_json_form_generator_string_field(self):
    logging.info('Starting %s' % inspect.stack()[0][3])

    elem = JSONStringField("name", {
        "type": "string",
        "description": "First and Last name",
        "minLength": 4,
        "default": "John Doe"
      })
    self.assertDictEqual(elem.getData(), {"name": "John Doe"})

  def test_json_form_generator_enum(self):
    logging.info('Starting %s' % inspect.stack()[0][3])

    elem = JSONEnumField("Field of MRI scanner", {
        "type": "string",
        "enum": [
          "1.5T",
          "3T"
        ]
      })
    self.assertIsInstance(elem.getElement(), qt.QComboBox)

    elem = JSONEnumField("Field of MRI scanner", {
        "type": "string",
        "ui:widget": "combo",
        "enum": [
          "1.5T",
          "3T"
        ]
      })
    self.assertIsInstance(elem.getElement(), qt.QComboBox)

    elem = JSONEnumField("Field of MRI scanner", {
        "type": "string",
        "ui:widget": "radio",
        "enum": [
            "1.5T",
            "3T"
          ]
      })
    self.assertIsInstance(elem.getElement(), qt.QFrame)

  def test_json_form_generator_integer_type(self):
    logging.info('Starting %s' % inspect.stack()[0][3])

    elem = JSONIntegerField("age", {
        "type": "integer",
        "default": 25,
        "minimum": 18,
        "maximum": 99
      })

    self.assertDictEqual(elem.getData(), {"age": 25})
    self.assertEqual(elem._validator.bottom, 18)
    self.assertEqual(elem._validator.top, 99)

  def test_json_form_generator_object_field(self):
    logging.info('Starting %s' % inspect.stack()[0][3])

    import os
    path = os.path.join(os.path.dirname(os.path.normpath(os.path.dirname(inspect.getfile(FormGeneratorFactory)))),
                        "test_schema.json")

    formGenerator = FormGeneratorFactory.getFormGenerator(path)
    form = formGenerator.generate()
    dataPath = os.path.join(os.path.dirname(os.path.normpath(os.path.dirname(inspect.getfile(FormGeneratorFactory)))),
                            "test_data.json")
    with open(dataPath) as data_file:
      import json
      expected = json.load(data_file)
      self.maxDiff = None
      self.assertDictEqual(form.getData(), expected)