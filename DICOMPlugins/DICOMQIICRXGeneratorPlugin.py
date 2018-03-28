import slicer
import logging
import os
import ctk
from datetime import datetime
import json

from SlicerPIRADSLogic.SeriesType import *
from SlicerPIRADSLogic.Exception import StudyNotEligibleError
from SlicerDevelopmentToolboxUtils.mixins import ModuleLogicMixin


class DICOMQIICRXGeneratorPluginClass(object):

  TAGS = {
    'modality': '0008,0060',
    'seriesDescription': '0008,103E',
    'seriesInstanceUID': '0020,000E'
  }

  @property
  def currentDateTime(self):
    try:
      return self._currentDateTime
    except AttributeError:
      self._currentDateTime = datetime.now().strftime('%Y-%m-%d_%H%M%S')
    return self._currentDateTime

  @property
  def db(self):
    return slicer.dicomDatabase

  def __init__(self):
    try:
      slicer.modules.qiicrxsr
    except AttributeError as exc:
      raise AttributeError("{}\nMake sure to install extension DCMQI".format(exc.message))
    self.tempDir = os.path.join(slicer.app.temporaryPath, "QIICRX", self.currentDateTime)
    self.modulePath = os.path.dirname(slicer.util.modulePath("SlicerPIRADS"))

  def generateReport(self, studyID):
    try:
      params = self._generateJSON(studyID)
    except StudyNotEligibleError:
      logging.error("Study with id '%s' is not eligible for PIRADS reading" % studyID)
      return

    outputSRPath = os.path.join(self.tempDir, "sr.dcm")
    params.update({
      "outputFileName": outputSRPath
    })

    logging.debug(params)
    cliNode = slicer.cli.run(slicer.modules.qiicrxsr, None, params, wait_for_completion=True)

    if cliNode.GetStatusString() != 'Completed':
      raise Exception("qiicrxsr CLI did not complete cleanly")
    else:
      indexer = ctk.ctkDICOMIndexer()
      indexer.addFile(slicer.dicomDatabase, outputSRPath, "copy")

  def _generateJSON(self, studyID):
    eligibleSeries = self.getEligibleSeriesForStudy(studyID)

    if not eligibleSeries:
      raise StudyNotEligibleError

    data = self._getGeneralMetaInformation()
    data['imageLibrary'] = []

    params = {
      "metaDataFileName": os.path.join(self.tempDir, "meta.json")
    }
    acqTypes = self._getAcquisitionTypes()
    data["compositeContext"], params["compositeContextDataDir"] = self._populateCompositeContext(eligibleSeries)

    seriesDirs = set(os.path.dirname(os.path.abspath(self.db.filesForSeries(series)[0])) for series in eligibleSeries)
    for series in eligibleSeries:
      try:
        data['imageLibrary'].append(self._createImageLibraryEntry(series, acqTypes, len(seriesDirs) > 1))
      except ValueError as exc:
        print exc.message

    params["imageLibraryDataDir"] = os.path.commonprefix(seriesDirs)

    if not os.path.exists(self.tempDir):
      ModuleLogicMixin.createDirectory(self.tempDir)
    with open(params['metaDataFileName'], 'w') as outfile:
      json.dump(data, outfile, indent=2)

    return params

  def _getAcquisitionTypes(self):
    with open(os.path.join(self.modulePath, 'Resources', 'ProstateMRIAcquisitionTypes.json')) as acqTypeFile:
      return json.load(acqTypeFile)

  def _populateCompositeContext(self, allSeries):
    f = self.db.filesForSeries(allSeries[0])[0]
    return os.path.basename(f), os.path.dirname(os.path.abspath(f))

  def _getGeneralMetaInformation(self):
    return {
      "SeriesDescription": "PI-RADS Report",
      "SeriesNumber": "1001",
      "InstanceNumber": "1",
    }

  def _createImageLibraryEntry(self, series, acqTypes, organizedInDirectories):
    data = dict()
    files = self.db.filesForSeries(series)
    seriesType = SeriesTypeFactory.getSeriesType(files[0])
    if not seriesType:
      raise ValueError("No eligible series type found for series '%s' " %
                       self.db.fileValue(files[0], self.TAGS['seriesDescription']))
    data['piradsSeriesType'] = acqTypes[seriesType.getName()]
    if organizedInDirectories:
      data['inputDICOMDirectory'] = os.path.basename(os.path.dirname(files[0]))
    else:
      data['inputDICOMFiles'] = [os.path.basename(f) for f in files]
    return data

  @staticmethod
  def getEligibleSeriesForStudy(study):
    db = slicer.dicomDatabase
    series = db.seriesForStudy(study)
    validSeries = []
    for s in series:
      if SeriesTypeFactory.getSeriesType(db.filesForSeries(s)[0]):
        validSeries.append(s)
    return validSeries


class DICOMQIICRXGeneratorPlugin:
  """
  This class is the 'hook' for slicer to detect and recognize the plugin
  as a loadable scripted module
  """
  def __init__(self, parent):
    parent.title = "DICOM QIICRX Template Generator Plugin"
    parent.categories = ["Developer Tools.DICOM Plugins"]
    parent.contributors = ["Christian Herz (BWH), Andrey Fedorov (BWH)"]
    parent.helpText = """
    Plugin to the DICOM Module to generate DICOM QIICRX structured report instances.
    No module interface here, only in the DICOM module
    """
    parent.dependencies = ['DICOM', 'SlicerPIRADS']
    parent.acknowledgementText = """
    This DICOM Plugin was developed by
    Christian Herz and Andrey Fedorov, BWH.
    and was partially funded by NIH grant U24 CA180918 (QIICR).
    """