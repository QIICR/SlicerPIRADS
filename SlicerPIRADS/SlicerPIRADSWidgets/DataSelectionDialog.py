

import qt
import os
import slicer
import logging
from DICOMQIICRXLoaderPlugin import *


class DataSelectionDialog(qt.QDialog):
  """ TODO: generalize more and move to SDT """

  def __init__(self, parent=None):
    qt.QDialog.__init__(self, parent)
    self.modulePath = os.path.dirname(slicer.util.modulePath("SlicerPIRADS"))
    self.db = slicer.dicomDatabase
    self.modal = True
    self.setup()

  def setup(self):
    path = os.path.join(self.modulePath, 'Resources', 'UI', 'DataSelectionDialog.ui')
    self.ui = slicer.util.loadUI(path)
    self._browseButton = self.ui.findChild(qt.QPushButton, "browseButton")
    self._loadButton = self.ui.findChild(qt.QPushButton, "loadButton")
    self._selectAllButton = self.ui.findChild(qt.QPushButton, "selectAllButton")
    self._selectAllButton.enabled = False
    self._deselectAllButton = self.ui.findChild(qt.QPushButton, "deselectAllButton")
    self._deselectAllButton.enabled = False
    self._progress = self.ui.findChild(qt.QProgressBar, "progressBar")
    self._progress.hide()
    self._configurePatientTable()
    self._configureStudiesTable()
    self._configureSeriesTable()
    self._configureCommonTableSettings()
    self._setupConnections()

  def _configurePatientTable(self):
    self._patientTable = self.ui.findChild(qt.QTableView, "patientsTableView")
    self._patientTableModel = PatientsTableModel()
    self._patientTable.setModel(self._patientTableModel)
    self._patientTable.horizontalHeader().setSectionResizeMode(0, qt.QHeaderView.Stretch)
    self._patientTable.horizontalHeader().setSectionResizeMode(1, qt.QHeaderView.ResizeToContents)

  def _configureStudiesTable(self):
    self._studiesTable = self.ui.findChild(qt.QTableView, "studiesTableView")
    self._studiesTableModel = qt.QStandardItemModel()
    self._studiesTableModel.setHorizontalHeaderLabels(["Study Instance UID", "Date"])
    self._studiesTable.setModel(self._studiesTableModel)
    self._studiesTable.setEditTriggers(qt.QAbstractItemView.NoEditTriggers)
    self._studiesTable.horizontalHeader().setSectionResizeMode(0, qt.QHeaderView.Stretch)
    self._studiesTable.horizontalHeader().setSectionResizeMode(1, qt.QHeaderView.ResizeToContents)

  def _configureSeriesTable(self):
    self._seriesTable = self.ui.findChild(qt.QTableView, "seriesTableView")
    self._seriesTableModel = qt.QStandardItemModel()
    self._seriesTableModel.setHorizontalHeaderLabels(["UID", "Series Number", "Series Date", "Modality", "Series Description"])
    self._seriesTable.setModel(self._seriesTableModel)
    self._seriesTable.setEditTriggers(qt.QAbstractItemView.NoEditTriggers)
    self._seriesTable.setColumnHidden(0, True)
    # self._seriesTable.horizontalHeader().setSectionResizeMode(0, qt.QHeaderView.Stretch)
    self._seriesTable.horizontalHeader().setSectionResizeMode(1, qt.QHeaderView.ResizeToContents)
    self._seriesTable.horizontalHeader().setSectionResizeMode(2, qt.QHeaderView.ResizeToContents)
    self._seriesTable.horizontalHeader().setSectionResizeMode(3, qt.QHeaderView.ResizeToContents)
    self._seriesTable.horizontalHeader().setSectionResizeMode(4, qt.QHeaderView.Stretch)
    self._seriesTable.setSelectionBehavior(qt.QTableView.SelectRows)
    self._seriesTable.verticalHeader().hide()

  def _configureCommonTableSettings(self):
    for table in [self._studiesTable, self._patientTable]:
      table.setSelectionBehavior(qt.QTableView.SelectRows)
      table.setSelectionMode(qt.QTableView.SingleSelection)
      # table.horizontalHeader().setSectionResizeMode(qt.QHeaderView.Stretch)
      table.verticalHeader().hide()

  def _setupConnections(self):
    def setupConnections(funcName="connect"):
      getattr(self._browseButton.clicked, funcName)(self._onBrowseButtonClicked)
      getattr(self._loadButton.clicked, funcName)(self._onLoadButtonClicked)
      getattr(self._patientTable.selectionModel(), funcName)('currentChanged(QModelIndex, QModelIndex)',
                                                             self._onPatientSelected)
      getattr(self._studiesTable.selectionModel().selectionChanged, funcName)(self._onStudySelectionChanged)
      getattr(self._seriesTable.selectionModel().selectionChanged, funcName)(self._onSeriesSelectionChanged)
      getattr(self._selectAllButton.clicked, funcName)(lambda: self._selectAllSeries(True))
      getattr(self._deselectAllButton.clicked, funcName)(lambda: self._selectAllSeries(False))
    setupConnections()
    slicer.app.connect('aboutToQuit()', self.deleteLater)
    self.destroyed.connect(lambda : setupConnections(funcName="disconnect"))

  def _onPatientSelected(self, modelIndex):
    pid = self._patientTableModel.getPatients()[modelIndex.row()]
    self._fillStudiesList(pid)
    if self._studiesTableModel.rowCount() == 1:
      self._autoSelectFirstStudy()
    else:
      self._loadButton.enabled = False

  def _autoSelectFirstStudy(self):
    modelIndex = self._studiesTableModel.index(0, 0)
    self._studiesTable.selectionModel().select(modelIndex, qt.QItemSelectionModel.Select | qt.QItemSelectionModel.Rows)

  def _fillStudiesList(self, pid):
    self._studiesTableModel.removeRows(0, self._studiesTableModel.rowCount())
    studies = self._patientTableModel.getStudiesForPatient(pid)
    for study in studies:
      series = self.db.seriesForStudy(study)
      self._studiesTableModel.appendRow([qt.QStandardItem(study),
                                         qt.QStandardItem(self.db.fileValue(self.db.filesForSeries(series[0])[0],
                                                                            "0008,0020") if len(series) else "")])
    self._studiesTable.horizontalHeader().setSectionResizeMode(1, qt.QHeaderView.ResizeToContents)

  def _fillSeriesList(self, studyID):
    # TODO: add smart logic for row selection SR selection only one! if SR selected, don't allow selection of other series
    self._clearSeriesList()
    series = sorted(self.db.seriesForStudy(studyID), key=lambda a: int(self.db.fileValue(self.db.filesForSeries(a)[0],
                                                                                '0020,0011')))
    for rowIdx, s in enumerate(series):
      info = [qt.QStandardItem(s)]
      for tag in ['0020,0011', '0008,0023', '0008,0060', '0008,103E']:
        item = qt.QStandardItem(self.db.fileValue(self.db.filesForSeries(s)[0], tag))
        info.append(item)
      self._seriesTableModel.appendRow(info)
    self._seriesTable.horizontalHeader().setSectionResizeMode(1, qt.QHeaderView.ResizeToContents)
    self._seriesTable.horizontalHeader().setSectionResizeMode(3, qt.QHeaderView.ResizeToContents)
    self._selectAllButton.enabled = self._seriesTableModel.rowCount() > 0
    self._deselectAllButton.enabled = self._seriesTableModel.rowCount() > 0

  def _clearSeriesList(self):
    self._seriesTableModel.removeRows(0, self._seriesTableModel.rowCount())

  def _selectAllSeries(self, selected):
    if selected:
      m = self._seriesTableModel
      itemSelection = \
        qt.QItemSelection(m.index(0, 0), m.index(m.rowCount()-1, m.columnCount()-1))
      self._seriesTable.selectionModel().select(itemSelection, qt.QItemSelectionModel.Select | qt.QItemSelectionModel.Rows)
    else:
      self._seriesTable.selectionModel().clearSelection()

  def _onStudySelectionChanged(self, current, previous):
    # TODO: cache information of `is eligible` so that it doesn't need to be recalculated every single time selection changes
    if current.indexes():
      study = self._studiesTableModel.data(current.indexes()[0])
      # self._loadButton.enabled = DICOMQIICRXLoaderPluginClass.hasEligibleQIICRXReport(study) or \
      #                            len(DICOMQIICRXLoaderPluginClass.getEligibleSeriesForStudy(study))
      self._fillSeriesList(study)
      # TODO: preselect eligible series... and if there is an eligible SR the most recent one!

  def _onSeriesSelectionChanged(self, selected, deselected):
    # TODO: series selection and SR selection should not be possible at the same time
    indexes = self._seriesTable.selectionModel().selectedIndexes
    selectedRows = set([index.row() for index in indexes])
    self._loadButton.enabled = len(selectedRows)

  def _onLoadButtonClicked(self):
    indexes = self._seriesTable.selectionModel().selectedIndexes
    m = self._seriesTableModel
    uids = [m.data(m.index(row, 0)) for row in set([index.row() for index in indexes])]

    # TODO: right now only expecting one report to be in the study
    qiicrxReportSeries = DICOMQIICRXLoaderPluginClass.getQIICRXReportSeries(uids)
    # TODO: if list of eligible SRs is longer, get the most recent one!

    if qiicrxReportSeries:
      self._loadReport(qiicrxReportSeries)
      self.ui.accept()
    else:
      DICOMQIICRXGenerator().generateReport(uids)
      study = self._studiesTableModel.data(self._studiesTable.selectionModel().selectedIndexes[0])
      self._fillSeriesList(study)

      # series = DICOMQIICRXLoaderPluginClass.getEligibleSeriesForStudy(studyId)
      # self._progress.setMaximum(len(series))
      # self._progress.show()
      #
      # for idx, s in enumerate(series):
      #   files = slicer.dicomDatabase.filesForSeries(s)
      #   self._progress.setValue(idx)
      #   slicer.app.processEvents()
      #   DICOMQIICRXLoaderPluginClass.loadSeries(files)

  def _loadReport(self, qiicrxReportSeries):
    """ Load report from existing qiicrx report series

    Args:
      qiicrxReportSeries: seriesInstanceUID of the qiicrx report series to be loaded

    Todo:
      report progress

    """
    qiicrxReportSeries = sorted(qiicrxReportSeries,
                                key=lambda s: int(self.db.fileValue(self.db.filesForSeries(s)[0], '0008,0021'))+
                                              int(self.db.fileValue(self.db.filesForSeries(s)[0], '0008,0031')),
                                reverse=True)
    if len(qiicrxReportSeries) > 1:
      logging.info("Found multiple QIICRX reports: loading latest one.")

    loader = DICOMQIICRXLoaderPluginClass()
    loadables = loader.examineFiles(slicer.dicomDatabase.filesForSeries(qiicrxReportSeries[0]))
    if loadables:
      loader.load(loadables[0])

  def _onBrowseButtonClicked(self):
    path = qt.QFileDialog.getExistingDirectory(self.window(), "Select folder")
    if len(path):
      self._patientTable.update()

  def exec_(self):
    return self.ui.exec_()


class PatientsTableModel(qt.QAbstractTableModel):

  COLUMN_NAME = 'Patient Name'
  COLUMN_DOB = 'Date of Birth'

  headers = [COLUMN_NAME, COLUMN_DOB]

  @property
  def db(self):
    return slicer.dicomDatabase

  def __init__(self, parent=None, *args):
    qt.QAbstractTableModel.__init__(self, parent, *args)
    self._datasets = dict()

  def rowCount(self):
    return len(self.getPatients())

  def columnCount(self):
    return len(self.headers)

  def headerData(self, col, orientation, role):
    if orientation == qt.Qt.Horizontal and role in [qt.Qt.DisplayRole, qt.Qt.ToolTipRole]:
        return self.headers[col]
    return None

  def data(self, index, role):
    if role != qt.Qt.DisplayRole:
      return None

    col = index.column()

    pid = self.getPatients()[index.row()]

    if col == 0:
      return self._getPatientName(pid)
    elif col == 1:
      return self._getPatientBirthDate(pid)

  def getPatients(self):
    return self.db.patients()

  def _getPatientName(self, pid):
    return self.db.fileValue(self._getDataset(pid), "0010,0010")

  def _getPatientBirthDate(self, pid):
    return self.db.fileValue(self._getDataset(pid), "0010,0030")

  def _getDataset(self, pid):
    try:
      return self._datasets[pid]
    except KeyError:
      studies = self.getStudiesForPatient(pid)
      series = self.db.seriesForStudy(studies[0])
      self._datasets[pid] = self.db.filesForSeries(series[0])[0]
    return self._datasets[pid]

  def getStudiesForPatient(self, pid):
    return self.db.studiesForPatient(pid)