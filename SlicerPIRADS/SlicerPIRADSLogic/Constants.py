from collections import OrderedDict


PIRADS_SCORE = OrderedDict([(1, "very low (clinically significant cancer is highly unlikely to be present)"),
                            (2, "low (clinically significant cancer is unlikely to be present)"),
                            (3, "intermediate (the presence of clinically significant cancer is equivocal)"),
                            (4, "high (clinically significant cancer is likely to be present)"),
                            (5, "very high (clinically significant cancer is highly likely to be present)")])

PZ_T2_TOOLTIPS = OrderedDict([(1, "(uniform hyperintense signal)"),
                              (2, "(Linear, wedge-shaped, diffuse, or indistinct hypointensity)"),
                              (3, "(Heterogeneous or non-circumscribed round moderate hypointensity)"),
                              (4, "(Circumscribed homogeneous moderate hypointense mass confined to prostate; <1.5 cm)"),
                              (5, "(Circumscribed homogeneous moderate hypointense mass confined to prostate; >= 1.5 "
                                  "cm or definite invasion/EPE)")])

PZ_DWI_TOOLTIPS = OrderedDict([(1, "(no abnormality on ADC or ultra high b images)"),
                               (2, "(indistinct or geographic decreased ADC or increased ultra high b-value signal)"),
                               (3, "(focal mild/moderate decreased ADC and normal or mild increased ultra high b-value"
                                   " signal)"),
                               (4, "(focal marked decreased ADC and marked increased ultra high b-value signal; <1.5 "
                                   "cm)"),
                               (5, "(focal marked decreased ADC and marked increased ultra high b-value signal; >=1.5 "
                                   "cm or definite invasion/EPE)")])

PZ_DCE_TOOLTIPS = OrderedDict([("(+)", "Focal early enhancement with edges matching lesion on other sequences"),
                               ("(-)", "No or diffuse early enhancement, or enhancement in area with BPH features")])

TZ_T2_TOOLTIPS = OrderedDict([(1, "(normal)"),
                              (2, "(circumscribed/encapsulated hypointense nodule; mildly atypical BPH)"),
                              (3, "(hypointense with obscured margins, not contained within a BPH nodule)"),
                              (4, "(lenticular or non-circumscribed homogeneous moderate decreased signal; <1.5 cm)"),
                              (5, "(lenticular or non-circumscribed homogeneous moderate decreased signal; >=1.5 cm or "
                                  "definite invasion/extra-prostatic extension)")])

TZ_DWI_TOOLTIPS = OrderedDict([(1, "(no abnormality on ADC or ultra high b images)"),
                               (2, "(indistinct or geographic decreased ADC)"),
                               (3, "(focal mild/moderate decreased ADC and normal or mild increased ultra high b-value "
                                   "signal)"),
                               (4, "(focal marked decreased ADC and marked increased ultra high b-value signal; <1.5 "
                                   "cm)"),
                               (5, "(focal marked decreased ADC and marked increased ultra high b-value signal; >=1.5 "
                                   "cm or definite invasion/extra-prostatic extension)")])

HTML_FORMATTED_TOOLTIP = """
  <html>
    <head>
      <style type="text/css"> </style>
    </head>
    <body style="font-family:'Lucida Grande',sans-serif; font-size: 12pt; font-weight: 400; font-style: normal;border: 1px solid black;margin-top:0px;">
      <table cellspacing=5>
        <tbody>
          {}
        </tbody>
      </table>
    </body>
  </html>
  """

HTML_FORMATTED_ROW = """
  <tr>
    <td><strong>{}</strong></td>
    <td>{}</td>
  </tr>"""