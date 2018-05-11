from .Finding import Finding


class PIRADSAssessmentCategory(object):
  # implement this as list
  # TODO: introduce event for changes on findings

  def __init__(self, findings=None):
    self._findings = findings if findings else []
    self._calculateAssessmentCategory()

  def __len__(self):
    return len(self._findings)

  def setFindings(self, findings):
    self._findings = findings
    self._calculateAssessmentCategory()

  def getFindings(self):
    return self._findings

  def addFinding(self, finding):
    assert isinstance(finding, Finding)
    self._findings.append(finding)
    self._calculateAssessmentCategory()

  def removeFinding(self, finding):
    if not finding in self._findings:
      return
    index = self._findings.index(finding)
    self._findings.pop(index)
    self._calculateAssessmentCategory()
    return index

  def getAssessmentCategory(self):
    # Makes only sense if up to date
    return self._assessmentCategory

  def _calculateAssessmentCategory(self):
    self._assessmentCategory = None
    if not self._findings:
      return
    # TODO: calculate