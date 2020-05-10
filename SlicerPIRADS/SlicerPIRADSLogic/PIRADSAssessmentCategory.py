from SlicerPIRADSLogic.Finding import Finding


class PIRADSAssessmentCategory(object):
  # TODO: introduce event for changes on findings

  def __init__(self, findings=None):
    self._findings = findings if findings else []
    self._calculateAssessmentCategory()
    self._dataChanged = True

  def __len__(self):
    return len(self._findings)

  def setFindings(self, findings):
    self._findings = findings
    self._dataChanged = True

  def getFindings(self):
    return self._findings

  def addFinding(self, finding):
    assert isinstance(finding, Finding)
    self._findings.append(finding)
    self._dataChanged = True

  def removeFinding(self, finding):
    if not finding in self._findings:
      return
    index = self._findings.index(finding)
    self._findings.pop(index)
    self._dataChanged = True
    return index

  def getAssessmentCategory(self):
    if self._dataChanged:
      self._calculateAssessmentCategory()
      self._dataChanged = False
    return self._assessmentCategory

  def _calculateAssessmentCategory(self):
    self._assessmentCategory = None
    if not self._findings:
      return
    for finding in self._finding:
      assessmentScores = finding.getAssessmentScores()
      print(assessmentScores)
      # TODO: calculate