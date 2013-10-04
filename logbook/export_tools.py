from reportlab.pdfgen import canvas
from pyPdf import PdfFileWriter, PdfFileReader
import StringIO
from reportlab.lib.pagesizes import letter
import os
import random
import datetime

 
def generate_pdf(id_string, user):
    from odk_viewer.models import ParsedInstance  #, DataDictionary

    #################
    # TODO filter on permit num, geographic location??
    pis = ParsedInstance.objects.filter(instance__user=user,
                                        instance__xform__id_string=id_string,)
                                        #lat__isnull=False, lng__isnull=False)

    # TODO lots of mock data, needs to be derived from DB
    obs_data = [ 
        {
          'permit_num': pi.to_dict()['obs_nm'],
          'species': random.choice(['King Salmon', 'Chum Salmon']),
          'date': pi.to_dict()['today'],
          'lat': pi.lat,
          'lng': pi.lng,
          'spawning': 2,
          'rearing': 3,
          'present': 4,
          'anadromous': True
        }
       for pi in pis
    ]

    meta = {
        'region': "Region 1",
        'quad': "Sneak Peak",
        'awc_num': '1234',
        'awc_name': "Salt Creek", 
        'awc_name_type': random.choice(['USGS', 'local']),
        'nomination_type': random.choice(['addition', 'deletion', 'correction', 'backup']),
        'user': user.get_username(),   # TODO lookup full name from the user profile
        'agency': "Alaska DFG",
        'addr1': "1255 W 8th St",
        'addr2': "Juneau, AK 99802",
        'today': datetime.datetime.now().strftime("%Y-%m-%d")
    }


    # Create pdf
    packet = StringIO.StringIO()
    can = canvas.Canvas(packet)

    # render a new PDF with Reportlab
    can = canvas.Canvas(packet, pagesize=letter)
    can.setFont('Courier', 9)

    # render metadata
    hs = [696, 673, 650, 631]
    can.drawString(120, hs[0] , meta['region'])
    can.drawString(380, hs[0], meta['quad'])
    can.drawString(270, hs[1], meta['awc_num'])
    can.drawString(160, hs[2], meta['awc_name'])

    if meta['awc_name_type'] == 'USGS':
        can.drawString(363, hs[2]+3, u"\u2713")
    elif meta['awc_name_type'] == 'local':
        can.drawString(466, hs[2]+3, u"\u2713")

    if meta['nomination_type'] == 'addition':
        can.drawString(59, hs[3], u"\u2713")
    elif meta['nomination_type'] == 'deletion':
        can.drawString(135, hs[3], u"\u2713")
    elif meta['nomination_type'] == 'correction':
        can.drawString(220, hs[3], u"\u2713")
    elif meta['nomination_type'] == 'backup':
        can.drawString(291, hs[3], u"\u2713")

    can.drawString(220, 190, meta['user'])
    can.drawString(220, 160, meta['agency'])
    can.drawString(220, 145, meta['addr1'])
    can.drawString(220, 130, meta['addr2'])
    can.drawString(450, 175, meta['today'])


    # render observational data
    for i, sd in enumerate(obs_data):
        height = 422 - 15*i
        can.drawString(40, height, sd['species'])
        can.drawString(150, height, sd['date'])
        can.drawString(295, height, str(sd['spawning']))
        can.drawString(360, height, str(sd['rearing']))
        can.drawString(440, height, str(sd['present']))
        if sd['anadromous']:
            can.drawString(502, height, u"\u2713")
        # can.drawString(150, height, str(sd['lat']))
        # can.drawString(250, height, str(sd['lng']))
    # can.drawString(10, 100, json.dumps(data_for_template, indent=2))
    can.save()

    #move to the beginning of the StringIO buffer
    packet.seek(0)
    new_pdf = PdfFileReader(packet)

    # read your existing PDF
    orig = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                        "original.pdf")
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