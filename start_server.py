#!/usr/bin/env python3

from flask import Flask,render_template,request,redirect,url_for,send_file
import os
from glob import glob
import subprocess
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization,hashes
from cryptography import x509
from cryptography.x509.oid import NameOID
import datetime



def create_key():
    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    with open("key.pem", "wb") as f:
        f.write(key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        ))
    return(key)

def create_cert(key):
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, u"GB"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, u""),
        x509.NameAttribute(NameOID.LOCALITY_NAME, u""),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"obj-webvr-viewer"),
        x509.NameAttribute(NameOID.COMMON_NAME, u"https://github.com/D6809e/obj-webvr-viewer"),
    ])
    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.datetime.utcnow()
    ).not_valid_after(
        datetime.datetime.utcnow() + datetime.timedelta(days=10)
    ).add_extension(
        x509.SubjectAlternativeName([x509.DNSName(u"localhost")]),
        critical=False,
    ).sign(key, hashes.SHA256())
    with open("cert.pem", "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))
    return(cert)


app = Flask(__name__)

@app.route('/index.html', methods=['GET'])
@app.route('/', methods=['GET'])
def index():
    #get all gltf files but strip the gltf suffix
    print("INDEX")
    scenes=list(map(lambda x: x.replace('.gltf',''),os.listdir('gltf')))
    return render_template('index.html',title='Scenes',scenes=scenes)

@app.route('/view', methods=['GET'])
def view():
    gltf_file = request.args.get('scene',default='*',type= str)
    return render_template('view.html',title='View',gltf_file=gltf_file)

#save uploaded files, convert to gltf
@app.route('/process', methods=['POST'])
def do_post():
    print("Uploading files..")
    if not os.path.isdir('TMP'):
        os.mkdir('TMP')
    for file in request.files.getlist('files[]'):
        print(file.filename)
        file.save('TMP/'+file.filename)
        print("Saved "+file.filename)
    obj_filename=glob('TMP/*.obj')[0]
    gltf_filename=obj_filename.replace('TMP','gltf').replace('obj','gltf')
    print("Processing to GLTF..")
    gltf_process = subprocess.Popen(['obj2gltf','-i',obj_filename,'-o',gltf_filename],stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out,err = gltf_process.communicate()
    for file in request.files.getlist('files[]'):
        os.remove('TMP/'+file.filename)
    print("Finished")
    return redirect(url_for('index'))

#Let's not allow the SSL key  or cert to be downloded..
@app.route('/key.pem',methods=['GET'])
@app.route('/cert.pem',methods=['GET'])
def do_nothing():
    return 'Nope'

@app.route('/<path:path>', methods=['GET'])
def serve_page(path):
    return send_file(path)


if __name__ == '__main__':
    key=create_key()
    create_cert(key)
    context = ('cert.pem', 'key.pem')
    app.run(host="0.0.0.0",port=8080, ssl_context=context)
    
