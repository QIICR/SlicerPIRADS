import re

from SlicerPIRADSLogic.SeriesType import *
from SlicerPIRADSLogic.Constants import *

from SlicerDevelopmentToolboxUtils.widgets import RadioButtonChoiceMessageBox


class LesionAssessmentRule(object):
  """ Base class for lesion based rules
  """

  PATTERN = None
  PREFERRED_MEASUREMENT_SERIES_TYPES = None
  PREFERRED_SERIES_TYPES_TOOLTIPS = {}

  def __init__(self):
    if not self.PATTERN:
      raise NotImplementedError("Class member 'PATTERN' must be defined by all inheriting classes")

  @staticmethod
  def isApplicable(sectors):
    raise NotImplementedError

  @classmethod
  def getPickList(cls, seriesType):
    raise NotImplementedError

  @classmethod
  def getPickListTooltip(cls, seriesType):
    for seriesTypeClass in cls.PREFERRED_SERIES_TYPES_TOOLTIPS.keys():
      if isinstance(seriesType, seriesTypeClass):
        data = cls.PREFERRED_SERIES_TYPES_TOOLTIPS[seriesTypeClass]
        return HTML_FORMATTED_TOOLTIP.format("\n".join([HTML_FORMATTED_ROW.format(key, value) for key,value in data.items()]))
    return ""


class TZRule(LesionAssessmentRule):

  PATTERN = r'^TZ'
  PREFERRED_MEASUREMENT_SERIES_TYPES = [T2BasedSeriesType, DiffusionBasedSeriesType]
  PREFERRED_SERIES_TYPES_TOOLTIPS = {T2BasedSeriesType: TZ_T2_TOOLTIPS,
                                     DiffusionBasedSeriesType: TZ_DWI_TOOLTIPS}
  @classmethod
  def isApplicable(cls, sectors):
    return any(re.match(cls.PATTERN, s) for s in sectors)

  @classmethod
  def getPickList(cls, seriesType):
    if any(isinstance(seriesType, c) for c in cls.PREFERRED_MEASUREMENT_SERIES_TYPES):
      return [1,2,3,4,5]
    return []


class PZRule(LesionAssessmentRule):

  PATTERN = r'^PZ'
  PREFERRED_MEASUREMENT_SERIES_TYPES = [T2BasedSeriesType, DiffusionBasedSeriesType, DCEBasedSeriesType]
  PREFERRED_SERIES_TYPES_TOOLTIPS = {T2BasedSeriesType: PZ_T2_TOOLTIPS,
                                     DiffusionBasedSeriesType: PZ_DWI_TOOLTIPS,
                                     DCEBasedSeriesType: PZ_DCE_TOOLTIPS}

  @classmethod
  def isApplicable(cls, sectors):
    return any(re.match(cls.PATTERN, s) for s in sectors)

  @classmethod
  def getPickList(cls, seriesType):
    if any(isinstance(seriesType, c) for c in cls.PREFERRED_MEASUREMENT_SERIES_TYPES):
      if isinstance(seriesType, DCEBasedSeriesType):
        return ["+", "-"]
      return [1,2,3,4,5]
    return []


class CZRule(LesionAssessmentRule):

  PATTERN = r'^CZ'

  @classmethod
  def isApplicable(cls, sectors):
    return any(re.match(cls.PATTERN, s) for s in sectors) or \
           (TZRule.isApplicable(sectors) and PZRule.isApplicable(sectors))


class LesionAssessmentRuleFactory(object):
  """ LesionAssessmentRuleFactory offers a static method for applying lesion assessment rules depending on its location
  """

  LesionAssessmentRules = [TZRule, PZRule]

  @classmethod
  def getEligibleLesionAssessmentRule(cls, sectors):
    """ Returns LesionAssessmentRule for a list of sectors

    Args:
      sectors: list of sectors selected from ProstateSectorMapDialog

    Returns:
      LesionAssessmentRule: instance of LesionAssessmentRule

    """
    def processUserPrompt(value):
      if not value:
        return None
      for assessmentRule in cls.LesionAssessmentRules:
        if re.match(assessmentRule.PATTERN, value):
          return assessmentRule()

    if CZRule.isApplicable(sectors):
      return processUserPrompt(RadioButtonChoiceMessageBox("Which rule do you want to use?",
                                                           options=["TZ", "PZ"]).exec_())
    elif TZRule.isApplicable(sectors):
      return TZRule()
    elif PZRule.isApplicable(sectors):
      return PZRule()
    return None

