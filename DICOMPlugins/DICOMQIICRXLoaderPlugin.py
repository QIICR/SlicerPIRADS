import slicer
import ctk
import dicom
import os
import json
import logging
from datetime import datetime

from DICOMLib import DICOMPlugin, DICOMLoadable
from MultiVolumeImporterPlugin import MultiVolumeImporterPluginClass
from DICOMScalarVolumePlugin import DICOMScalarVolumePluginClass

from SlicerPIRADSLogic.SeriesType import *
from SlicerPIRADSLogic.Exception import StudyNotEligibleError

from SlicerDevelopmentToolboxUtils.mixins import ModuleLogicMixin
from SlicerDevelopmentToolboxUtils.decorators import multimethod


class DICOMQIICRXMixin(ModuleLogicMixin):

  UID_EnhancedSRStorage = "1.2.840.10008.5.1.4.1.1.88.22"
  TEMPLATE_ID = "QIICRX"

  tags = {
    'modality': '0008,0060',
    'seriesDescription': '0008,103E',
    'seriesInstanceUID': '0020,000E',
    'classUID': '0008,0016',
    'templateIdentifier': '0040,DB00'
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

  @classmethod
  def isQIICRX(cls, dataset):
    try:
      return cls.getDICOMValue(dataset, "Modality") == 'SR' and \
             cls.getDICOMValue(dataset, "SOPClassUID") == cls.UID_EnhancedSRStorage and \
             cls.getDICOMValue(dataset, "ContentTemplateSequence")[0].TemplateIdentifier == cls.TEMPLATE_ID
    except (AttributeError, IndexError):
      return False


class DICOMQIICRXLoaderPluginClass(DICOMPlugin, DICOMQIICRXMixin):

  @staticmethod
  def getEligibleSeriesForStudy(study):
    db = slicer.dicomDatabase
    series = db.seriesForStudy(study)
    validSeries = []
    for s in series:
      if SeriesTypeFactory.getSeriesType(db.filesForSeries(s)[0]):
        validSeries.append(s)
    return validSeries

  @classmethod
  def hasEligibleQIICRXReport(cls, study):
    return cls.getQIICRXReportSeries(study) is not None

  @classmethod
  def isDicomTIDQIICRX(cls, fileName):
    if cls.getDICOMValue(fileName, cls.tags['modality']) == 'SR':
      return DICOMQIICRXLoaderPluginClass.isQIICRX(dicom.read_file(fileName))
    return False

  @staticmethod
  @multimethod([str, unicode])
  def getQIICRXReportSeries(study):
    return DICOMQIICRXLoaderPluginClass.getQIICRXReportSeries(slicer.dicomDatabase.seriesForStudy(study))

  @staticmethod
  @multimethod([tuple, list])
  def getQIICRXReportSeries(series):
    eligible = []
    for currentSeries in series:
      if DICOMQIICRXLoaderPluginClass.isDicomTIDQIICRX(slicer.dicomDatabase.filesForSeries(currentSeries)[0]):
        eligible.append(currentSeries)
    return eligible

  def __init__(self):
    try:
      slicer.modules.qiicrxsr
    except AttributeError as exc:
      raise AttributeError("{}\nMake sure to install extension DCMQI".format(exc.message))

    DICOMPlugin.__init__(self)
    self.loadType = "DICOM {}".format(self.TEMPLATE_ID)

  def examine(self, fileLists):
    loadables = []
    for files in fileLists:
      cachedLoadables = self.getCachedLoadables(files)
      if cachedLoadables:
        loadables += cachedLoadables
      else:
        loadablesForFiles = self.examineFiles(files)
        loadables += loadablesForFiles
        self.cacheLoadables(files, loadablesForFiles)

    loadables.sort(lambda x,y: self.seriesSorter(x,y))

    return loadables

  def examineFiles(self, files):
    loadables = []
    for currentFile in files:
      dataset = dicom.read_file(currentFile)

      uid = self.getDICOMValue(dataset, "SOPInstanceUID")
      if uid == "":
        return []

      seriesDescription = self.getDICOMValue(dataset, "SeriesDescription", "Unknown")

      if self.isQIICRX(dataset):
        loadable = DICOMLoadable()
        loadable.selected = True
        loadable.confidence = 0.95
        loadable.files = [currentFile]
        loadable.name = '{} - as a DICOM {} object'.format(seriesDescription, self.TEMPLATE_ID)
        loadable.tooltip = loadable.name
        loadable.selected = True
        loadable.confidence = 0.95
        loadable.uids = [uid]
        loadables.append(loadable)

        logging.debug('DICOM SR {} modality found'.format(self.TEMPLATE_ID))

    return loadables

  def load(self, loadable):

    uid = loadable.uids[0]
    self.tempDir = os.path.join(slicer.app.temporaryPath, self.TEMPLATE_ID, self.currentDateTime)
    if not os.path.exists(self.tempDir):
      ModuleLogicMixin.createDirectory(self.tempDir)

    outputFile = os.path.join(self.tempDir, "{}.json".format(uid))

    srFileName = self.db.fileForInstance(uid)
    if srFileName is None:
      logging.debug('Failed to get the filename from the DICOM database for ', uid)
      return False

    param = {
      "inputDICOM": srFileName,
      "metaDataFileName": outputFile,
    }

    cliNode = slicer.cli.run(slicer.modules.qiicrxsr, None, param, wait_for_completion=True)
    if cliNode.GetStatusString() != 'Completed':
      logging.debug('qiicrxsr did not complete successfully, unable to load DICOM {}'.format(self.TEMPLATE_ID))
      # self.cleanup()
      return False

    with open(outputFile) as metaFile:
      data = json.load(metaFile)
      for imageLibraryEntry in data['imageLibrary']:
        files = [self.db.fileForInstance(e) for e in imageLibraryEntry['instanceUIDs']]
        self.loadSeries(files)

    return True

  @staticmethod
  def loadSeries(files):
    scalarVolumePlugin = DICOMScalarVolumePluginClass()
    scalarLoadables = scalarVolumePlugin.examineFiles(files)

    multiVolumeImporterPlugin = MultiVolumeImporterPluginClass()
    multiVolumeLoadables = multiVolumeImporterPlugin.examineFiles(files)

    if multiVolumeLoadables and multiVolumeLoadables[0].confidence >= scalarLoadables[0].confidence:
      multiVolumeImporterPlugin.load(multiVolumeLoadables[0])
    else:
      scalarVolumePlugin.load(scalarLoadables[0])


class DICOMQIICRXGenerator(DICOMQIICRXMixin):
  """ DICOMQIICRXGenerator generates a qiicrx DICOM report from an existing studyID """

  def __init__(self):
    try:
      slicer.modules.qiicrxsr
    except AttributeError as exc:
      raise AttributeError("{}\nMake sure to install extension DCMQI".format(exc.message))
    self.tempDir = os.path.join(slicer.app.temporaryPath, "QIICRX", self.currentDateTime)
    self.modulePath = os.path.dirname(slicer.util.modulePath("SlicerPIRADS"))

  def generateReport(self, obj):
    """ Generates a qiicrx DICOM report from an existing studyID and adds resulting series to DICOMDatabase

    Args:
      obj: studyID or list of series UIDs that is used as the input for creating a qiicrx DICOM report

    Todo:
      add option to add predecessor
    """
    if type(obj) in [str, unicode]:
      seriesUIDs = DICOMQIICRXLoaderPluginClass.getEligibleSeriesForStudy(obj)
      if not seriesUIDs:
        raise StudyNotEligibleError
    elif type(obj) in [tuple, list]:
      seriesUIDs = obj
    else:
      raise ValueError("Value of type %s is not supported" % type(obj))

    try:
      params = self._generateJSON(seriesUIDs)
    except StudyNotEligibleError:
      logging.error("Series '%s' is not eligible for PIRADS reading" % seriesUIDs)
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
      indexer.addFile(self.db, outputSRPath, "copy")

  def _generateJSON(self, seriesUIDs):
    data = self._getGeneralMetaInformation()
    data['imageLibrary'] = []

    params = {
      "metaDataFileName": os.path.join(self.tempDir, "meta.json")
    }
    acqTypes = self._getAcquisitionTypes()
    data["compositeContext"], params["compositeContextDataDir"] = self._populateCompositeContext(seriesUIDs)

    seriesDirs = set(os.path.dirname(os.path.abspath(self.db.filesForSeries(series)[0])) for series in seriesUIDs)
    for series in seriesUIDs:
      try:
        data['imageLibrary'].append(self._createImageLibraryEntry(series, acqTypes, len(seriesDirs) > 1))
      except ValueError as exc:
        print exc

    if not data['imageLibrary']:
      raise ValueError("No eligible series has been found for PIRADS reading!")

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
                       self.db.fileValue(files[0], self.tags['seriesDescription']))
    data['piradsSeriesType'] = acqTypes[seriesType.getName()]
    if organizedInDirectories:
      data['inputDICOMDirectory'] = os.path.basename(os.path.dirname(files[0]))
    else:
      data['inputDICOMFiles'] = [os.path.basename(f) for f in files]
    return data


class DICOMQIICRXLoaderPlugin:
  """
  This class is the 'hook' for slicer to detect and recognize the plugin
  as a loadable scripted module
  """
  def __init__(self, parent):
    parent.title = "DICOM QIICRX Template Plugin"
    parent.categories = ["Developer Tools.DICOM Plugins"]
    parent.contributors = ["Christian Herz (BWH), Andrey Fedorov (BWH)"]
    parent.helpText = """
    Plugin to the DICOM Module to load DICOM QIICRX structured report instances.
    No module interface here, only in the DICOM module
    """
    parent.dependencies = ['DICOM']
    parent.acknowledgementText = """
    This DICOM Plugin was developed by Christian Herz (BWH) and Andrey Fedorov (BWH) and was partially funded by 
    NIH grant U24 CA180918 (QIICR).
    """

    try:
      slicer.modules.dicomPlugins
    except AttributeError:
      slicer.modules.dicomPlugins = {}
    slicer.modules.dicomPlugins['DICOMQIICRXLoaderPlugin'] = DICOMQIICRXLoaderPluginClass
