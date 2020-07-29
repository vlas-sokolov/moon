"""Dummy webserver doing handouts of Lunar elevation squares"""

from os import path
from flask import Flask
from flask import request, send_file
from moon import io as mio

app = Flask(__name__)

@app.route('/craters', methods=['GET'])
def logo():
    """Reprojects LOLA DEM around a requested crater and returns back a .tif"""

    crater_name = request.args.get('name')
    fname = path.join('webcache', crater_name.replace(' ', '_'))

    if not path.isfile(fname):
        mio.crater_cutout(crater_name, destNameOrDestDS=fname, format="GTIFF")

    return send_file(fname, attachment_filename=path.basename(fname),
                     mimetype='image/tiff')
