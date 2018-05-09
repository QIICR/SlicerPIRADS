import re

from .SeriesType import *
from .Constants import *

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
    seriesTypeClass = seriesType.__class__
    if seriesTypeClass in cls.PREFERRED_SERIES_TYPES_TOOLTIPS.keys():
      data = cls.PREFERRED_SERIES_TYPES_TOOLTIPS[seriesTypeClass]
      return HTML_FORMATTED_TOOLTIP.format("\n".join([HTML_FORMATTED_ROW.format(key, value) for key,value in data.items()]))
    return ""


class TZRule(LesionAssessmentRule):

  PATTERN = r'^TZ'
  PREFERRED_MEASUREMENT_SERIES_TYPES = [T2a, T2c, T2s, DWIb, DWI]
  PREFERRED_SERIES_TYPES_TOOLTIPS = {T2a: TZ_T2_TOOLTIPS, T2c: TZ_T2_TOOLTIPS, T2s: TZ_T2_TOOLTIPS,
                                     DWI: TZ_DWI_TOOLTIPS, DWIb: TZ_DWI_TOOLTIPS}
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
  PREFERRED_MEASUREMENT_SERIES_TYPES = [T2a, T2c, T2s, DWIb, DWI, DCE]
  PREFERRED_SERIES_TYPES_TOOLTIPS = {T2a: PZ_T2_TOOLTIPS, T2c: PZ_T2_TOOLTIPS, T2s: PZ_T2_TOOLTIPS,
                                     DWI: PZ_DWI_TOOLTIPS, DWIb: PZ_DWI_TOOLTIPS,
                                     DCE: PZ_DCE_TOOLTIPS}

  @classmethod
  def isApplicable(cls, sectors):
    return any(re.match(cls.PATTERN, s) for s in sectors)

  @classmethod
  def getPickList(cls, seriesType):
    if any(isinstance(seriesType, c) for c in cls.PREFERRED_MEASUREMENT_SERIES_TYPES):
      if isinstance(seriesType, DCE):
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

