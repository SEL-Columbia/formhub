from reportlab.pdfgen import canvas
import json
from pyPdf import PdfFileWriter, PdfFileReader
import StringIO
from reportlab.lib.pagesizes import letter
import os

 
def generate_pdf(id_string, user):
    from odk_viewer.models import ParsedInstance  #, DataDictionary
    # dd = DataDictionary.objects.get(id_string=id_string, user=user)
    pis = ParsedInstance.objects.filter(instance__user=user,
                                        instance__xform__id_string=id_string,)
                                        #lat__isnull=False, lng__isnull=False)
    data_for_template = [ 
        {
          'permit_num': pi.to_dict()['obs_nm'],
          'lat': pi.lat,
          'lng': pi.lng
        }
       for pi in pis
    ]

    # Create pdf
    packet = StringIO.StringIO()
    can = canvas.Canvas(packet)

    # render a new PDF with Reportlab
    can = canvas.Canvas(packet, pagesize=letter)
    can.drawString(10, 100, json.dumps(data_for_template, indent=2))
    can.save()

    #move to the beginning of the StringIO buffer
    packet.seek(0)
    new_pdf = PdfFileReader(packet)

    # read your existing PDF
    orig = os.path.join(os.path.dirname(os.path.abspath(__file__)), "original.pdf")
    existing_pdf = PdfFileReader(file(orig, "rb"))
    output = PdfFileWriter()
    # add the "watermark" (which is the new pdf) on the existing page
    page = existing_pdf.getPage(0)
    page.mergePage(new_pdf.getPage(0))
    output.addPage(page)

    # finally, return output
    outputStream = StringIO.StringIO()
    output.write(outputStream)

    final = outputStream.getvalue()
    outputStream.close()
    return final