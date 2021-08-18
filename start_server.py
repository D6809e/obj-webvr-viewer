#!/usr/bin/env python3

from flask import Flask,render_template,request,redirect,url_for,send_file
import os
from glob import glob
import subprocess

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
    context = ('cert.pem', 'key.pem')
    app.run(host="0.0.0.0",port=8080, ssl_context=context)
    
