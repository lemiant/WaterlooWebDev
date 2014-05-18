from flask import Flask, render_template, request, make_response
from jinja2 import TemplateNotFound
import json, os, threading, re
from datetime import datetime
from jinja2 import evalcontextfilter, Markup, escape
from werkzeug.utils import secure_filename
import time, random

app = Flask(__name__, static_folder='static', static_url_path='')


_paragraph_re = re.compile(r'(?:\r\n|\r|\n){2,}')

@app.template_filter()
@evalcontextfilter
def nl2br(eval_ctx, value):
    result = u'\n\n'.join(u'<p>%s</p>' % p.replace('\n', '<br \>\n') \
        for p in _paragraph_re.split(value))
    return Markup(result)


widgets = {
    'location': {'type': 'textarea'},
    'cover': {'type': 'img'},
    'phone': {'type': 'input'},
    "mon":  {'type': 'input'},
    "tues": {'type': 'input'},
    "wed": {'type': 'input'},
    "thurs":{'type': 'input'},
    "fri":  {'type': 'input'},
    "sat":  {'type': 'input'},
    "sun":  {'type': 'input'},
    "map":  {'type': 'map'},
    "logo": {'type': 'img'},
    "contact": {'type': 'textarea'},
    "menu": {'type': 'menu'}
}

def widget(**kwargs):
    def get(key):
        widget_type = widgets[key]['type']
        res = render_template('widgets/'+widget_type+'.html', widget=key, current=context.get(key), **kwargs)
        return Markup(res)
    return get

@app.route('/')
@app.route('/<route>', methods=['GET', 'POST'])
def router(route=''):
    global context, mode
    mode = request.args.get('mode') or request.cookies.get('mode') or 'view'
    print request.form.get('mode'), mode
    with open('db.json') as context_file:
        context = json.load(context_file)
    if route == 'alter':
        resp = alter(context)
    elif route == 'upload':
        resp = upload_img()
    elif route == '':
        resp = render('index.html', context)
    else:
        try:
            resp = render(route.strip('/')+'.html', context)
        except TemplateNotFound as e:
            return "404, Sorry bud"
    resp = make_response(resp)
    resp.set_cookie('mode', mode)
    return resp
    
        

def render(page, context):
        return render_template(page, widget=widget(mode=mode), mode=mode, **context)

def upload_img():
    extensions = ['.png', '.jpg', '.jpeg', '.gif', '.svg']
    print request.files
    file = request.files.get('value')
    if file:
        name, ext = os.path.splitext(file.filename.lower())
        if ext in extensions:
            path = '/ull/'+unique_name()+ext
            file.save('static'+path)
            return path
    
def random_string(len, chars="ABCDEFGHIJKLMNOPQRSTUZWXYZ"):
    return ''.join([random.choice(chars) for _ in range(len)])
def unique_name():
    return str(time.time()).replace('.','') + random_string(6)
    
def alter(context):
    widget_type = widgets[request.form['widget']]['type']
    if widget_type in ["input","textarea","map"]:
        value = request.form['value']
    elif widget_type == "menu":
        value = json.loads(request.form['value'])
    elif widget_type == "img":
        value = upload_img()
    context.update({request.form['widget']:value})
    save(context)
    
    if widget_type == "img": return value #Send back new url
    elif widget_type == "map": return render_template('widgets/map.html', current=value, widget='map')
    return 'yup'

def save(context):
    unique = 'backups/'+unique_name()+'.json'
    backup = 'backups/db-'+datetime.strftime(datetime.now(), '%Y_%m_%d_%H')+'.json'
    db = "db.json"
    with open(unique, 'w') as temp:
        temp.write(json.dumps(context))
    os.rename(unique, db)
    with open(unique, 'w') as temp:
        temp.write(json.dumps(context))
    os.rename(unique, backup)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)