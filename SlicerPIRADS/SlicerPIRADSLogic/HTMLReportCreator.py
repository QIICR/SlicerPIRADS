import os
import webbrowser

import slicer

from SlicerDevelopmentToolboxUtils.mixins import ModuleWidgetMixin, ModuleLogicMixin

from SlicerPIRADSWidgets.ProstateSectorMapDialog import ProstateSectorMapDialog


class HTMLReportCreator(object):
  style = '''
    body {
      font-family: Helvetica, Arial;
    }

    h2 {
      color: #2e6c80;
    }
    @media print {
      @page { size: auto;  margin: 7mm; }
      .print-friendly {
          page-break-inside: avoid;
      }
    }
  '''

  infoRow = '''
      <tr>
        <td class='heading'><b>{0}</b></td>
        <td>{1}</td>
      </tr>
    '''

  template = '''
      <html>
        <head>
        <meta name=\"Author\" content=\"...\">
        <title> Slicer PI-RADS Report </title>
        <style type=\"text/css\">{0}</style>
        <body>
          {1}
        </body> 
       </html>
    '''

  sectorMapScreenShot = '''
      <tr>
        <td>
          <img src="{}">
        </td>
      </tr>
  '''

  def __init__(self, assessmentCategory):
    self._assessmentCategory = assessmentCategory
    self.patientInfo = None

  def generateReport(self):

    def currentDateTime():
      from datetime import datetime
      return datetime.now().strftime('%Y-%m-%d_%H%M%S')

    html = self.template.format(self.style, self.getData())

    outputPath = os.path.join(slicer.app.temporaryPath, "SlicerProstate", "PI-RADS")
    if not os.path.exists(outputPath):
      ModuleLogicMixin.createDirectory(outputPath)
    outputHTML = os.path.join(outputPath, currentDateTime() + "_testReport.html")
    print(outputHTML)
    f = open(outputHTML, 'w')
    f.write(html)
    f.close()
    webbrowser.open("file:///private" + outputHTML)

  def getData(self):
    data = ""

    prostateMap = ProstateSectorMapDialog()
    prostateMap.displayCheckboxBorder(visible=False)

    for finding in self._assessmentCategory.getFindings():
      prostateMap.resetButtons()
      prostateMap.setSelectedSectors(finding.getSectors())
      prostateMap.setButtonsVisible(checkedOnly=True)

      data += '''
        <div class="print-friendly">
          <h2>{0}</h2>
          <table border=1 width='100%' cellPadding=3 cellSpacing=0>
            {1}
          </table>
          <br>
        </div>
        '''.format(finding.getName(),
                   "".join([self.sectorMapScreenShot.format(ModuleWidgetMixin.pixelmapAsRaw(pixmap))
                              for pixmap in prostateMap.getScreenShots()]))

    return data