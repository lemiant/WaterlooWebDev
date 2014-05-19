from flask import Flask, request, make_response, redirect, send_from_directory, render_template
from jinja2 import TemplateNotFound, evalcontextfilter, Markup, escape, Environment, FileSystemLoader
import json, os, threading, re
from datetime import datetime
from jinja2.filters import do_urlencode as urlencode
from werkzeug.utils import secure_filename
import time, random, shutil, hashlib
from happy_env import HappyEnv

app = Flask(__name__)
app.debug = True


_paragraph_re = re.compile(r'(?:\r\n|\r|\n){2,}')


def nl2br(value):
    result = u'\n\n'.join(u'<p>%s</p>' % p.replace('\n', '<br \>\n') \
        for p in _paragraph_re.split(value))
    return Markup(result)
        
@app.route('/', methods=['GET', 'POST'])
@app.route('/<path:route>', methods=['GET', 'POST'])
def meta_router(route=''):
    os.chdir('/vagrant')
    server = request.headers['Host'].split('.')[:-2]
    with open('sites.json') as sites_file:
        sites = json.load(sites_file)    
    site = sites[server[-1]]
    login = hashlib.sha1(site['pwd']).hexdigest() == request.cookies.get('pwd') 
    project_root = './sources/'+server[-1]+'/'
    context = json.load(open(project_root+'/db.json'))
    env = HappyEnv(project_root+'templates/')
    env.globals.update({'context':context, 'project_root':project_root, 'mode': 'view', 'editor': True, 'request': request, 'site': site})
    env.filters['nl2br'] = nl2br
    
    if len(server) == 1:
        if route == 'regenerate':
            if login:
                return regenerate_pages(env)
            else: return '', 403
        elif os.path.isfile('./static/'+route):
            return send_from_directory('static/', route)
        else:
            return render_template('editor.html', site=site)
    elif server[-1] in sites:
        mode = server[-2]
        if mode not in ['view', 'edit']: return "404, sorry bud (You're mode is wrong)", 404
        env.globals.update({'mode':mode})
        if route == 'login':
            if site['pwd'] == request.form.get('pwd'):
                resp = make_response(redirect('http://'+request.headers['Host']+request.args.get('target')))
                resp.set_cookie('pwd', hashlib.sha1(request.form.get('pwd')).hexdigest(), domain='.'+'.'.join(request.headers['Host'].split('.')[-3:]))
                return resp
            else:
                env.globals['mode'] = "view"
                return env.render('login.html')
        elif os.path.isfile(project_root+'static/'+route):
            return send_from_directory(project_root+'static/', route)
        elif not login:
            return redirect('http://'+request.headers['Host']+'/login?target='+urlencode(route))
        else:
            return core_router(route, env) or ("404, Sorry dude", 404)
        
def core_router(route, env):
    if route == 'alter':
        return alter(env)
    elif route == 'upload':
        return upload_img()
    elif route == '':
        return env.render('index.html')
    else:
        try:
            return env.render(route.strip('/')+'.html')
        except TemplateNotFound as e:
            return False 
    
def regenerate_pages(env):
    folder = env.globals['project_root']
    context = env.globals['context']
    env.globals.update({'editor': False})
    TEMPLATES_DIR = folder+'templates/'
    STATIC_DIR = folder+'static/'
    SITE_DIR = '../sites/tomusushi/'
    BUILD_DIR = 'builds/'+unique_name()+'/'
    shutil.copytree(STATIC_DIR, SITE_DIR+BUILD_DIR)
    for file in os.listdir(TEMPLATES_DIR):
        if 'login' in  file or 'base' in file: pass
        elif not os.path.isfile(TEMPLATES_DIR+file): pass
        else:
            with open(SITE_DIR+BUILD_DIR+file, 'w') as static:
                static.write(env.render(file).encode('ascii', 'xmlcharrefreplace'))
    LINK_NAME = unique_name()
    os.symlink(BUILD_DIR, SITE_DIR+LINK_NAME)
    os.rename(SITE_DIR+LINK_NAME, SITE_DIR+'current')
    builds = sorted(os.listdir(SITE_DIR+'builds/'), reverse=True)
    for build in builds[5:]:
        shutil.rmtree(SITE_DIR+'builds/'+build)
    return 'howdy'

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
    
def alter(env):
    context = env.globals['context']
    widget_type = request.form['type']
    if widget_type in ["input","textarea","map"]:
        value = request.form['value']
    elif widget_type == "menu":
        value = json.loads(request.form['value'])
    elif widget_type == "img":
        value = upload_img()
    save(dict(context.items() + [(request.form['key'], value)]), env.globals['project_root'])
    
    if widget_type == "img": return value #Send back new url
    elif widget_type == "map": return env.render('widgets/map.html', current=value, key=request.form['key'])
    return 'yup'

def save(context, folder):
    unique = folder+'backups/'+unique_name()+'.json'
    backup = folder+'backups/db-'+datetime.strftime(datetime.now(), '%Y_%m_%d_%H')+'.json'
    db = folder+"db.json"
    with open(unique, 'w') as temp:
        temp.write(json.dumps(context))
    os.rename(unique, db)
    with open(unique, 'w') as temp:
        temp.write(json.dumps(context))
    os.rename(unique, backup)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)