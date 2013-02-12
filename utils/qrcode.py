import StringIO
from elaphe import barcode
from base64 import b64encode

def generate_qrcode(message, stream=None,
                    eclevel='M', margin=10,
                    data_mode='8bits', format='PNG', scale=2.5):
    ''' Generate a QRCode, settings options and output '''

    if stream is None:
        stream = StringIO.StringIO()

    img = barcode('qrcode', message,
                  options=dict(version=9, eclevel=eclevel),
                  margin=margin, data_mode=data_mode, scale=scale)

    img.save(stream, format)

    datauri = "data:image/png;base64,%s" % b64encode(stream.getvalue())
    stream.close()
    return datauri
