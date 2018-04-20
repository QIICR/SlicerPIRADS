import unittest
import logging
import inspect

from SlicerPIRADSLogic.FormGeneratorFactory import FormGeneratorFactory
from SlicerPIRADSLogic.JSONFormGenerator import JSONFormGenerator


class FormGeneratorFactoryTests(unittest.TestCase):

  def test_right_generator(self):
    logging.info('Starting %s' % inspect.stack()[0][3])

    formGenerator = FormGeneratorFactory.getFormGenerator("/foo/bar/schema.json")
    self.assertIsInstance(formGenerator, JSONFormGenerator)

  def test_file_extension_not_supported(self):
    logging.info('Starting %s' % inspect.stack()[0][3])

    with self.assertRaises(ValueError):
      FormGeneratorFactory.getFormGenerator("/foo/bar/schema.xyz")

