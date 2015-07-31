from flask import Flask, request, make_response, redirect, send_from_directory, render_template
from jinja2 import TemplateNotFound, Markup, escape, Environment, FileSystemLoader
from jinja2.filters import do_urlencode as urlencode
import json, os, threading, re, time, random, shutil, hashlib
from datetime import datetime

app = Flask(__name__)
app.debug = True
file_dir = os.path.dirname(os.path.realpath(__file__))
os.chdir(file_dir)

main_env = Environment(loader=FileSystemLoader('./designs/main/templates/'))

class InvalidSite(Exception):
    pass
        
def get_env():  
    server = request.headers['Host'].split('.')[:-2]
    mode = server[-2] if len(server) > 1 else None
    site = server[-1]
    data_dir = './data/'+site+'/'
    if os.path.isdir(data_dir):
        context = json.load(open(data_dir+'db.json'))
        meta = context['meta']
        design_dir = './designs/'+meta['design']+'/' 
        authorized = hashlib.sha1(meta['password']).hexdigest() == request.cookies.get('pwd') 
        env = Environment(loader=FileSystemLoader(design_dir+'templates/'))
        env.globals.update({
            'context': context, 
            'meta': context['meta'],
            'data_dir': data_dir,
            'design_dir': design_dir,
            'isEditor': True,
            'authorized': authorized,
            'mode': mode,
            'request': request, 
            'site': site
        })
        env.filters['nl2br'] = nl2br
        return env
    else: raise InvalidSite()
    
@app.route('/', methods=['GET', 'POST'])
@app.route('/<path:route>', methods=['GET', 'POST'])
def meta_router(route=''):
    print route
    try:
        env = get_env()
    except InvalidSite:
        return "404, not a real site."
    
    if env.globals['mode'] is None:
        if route == 'regenerate':
            if env.globals['authorized']:
                return regenerate_pages(env)
            else: return '', 403
        elif os.path.isfile('./designs/main/static/'+route):
            return send_from_directory('./designs/main/static', route)
        else:
            return main_env.get_template('editor.html').render(**env.globals)
        
    else:
        if env.globals['mode'] not in ['view', 'edit']: return "404, sorry bud (You're mode is wrong)", 404
        if route == 'login':
            if env.globals['context']['meta']['password'] == request.form.get('pwd'):
                resp = make_response(redirect('http://'+request.headers['Host']+'/'+request.args.get('target')))
                resp.set_cookie('pwd', hashlib.sha1(request.form.get('pwd')).hexdigest(), domain='.'+'.'.join(request.headers['Host'].split('.')[-3:]))
                return resp
            else:
                return env.get_template('login.html').render()
        elif os.path.isfile(env.globals['data_dir']+route) and route.startswith('ull/'):
            return send_from_directory(env.globals['data_dir'], route)
        elif os.path.isfile(env.globals['design_dir']+'static/'+route):
            return send_from_directory(env.globals['design_dir']+'static/', route)
        elif not env.globals['authorized']:
            return redirect('http://'+request.headers['Host']+'/login?target='+urlencode(route))
        else:
            return core_router(route, env) or ("404, Sorry dude", 404)
        
    
def core_router(route, env):
    if route == 'alter':
        return alter(env)
    elif route == 'upload':
        return upload_img(env)
    elif route == '':
        return env.get_template('index.html').render()
    else:
        try:
            return env.get_template(route.strip('/')+'.html').render()
        except TemplateNotFound as e:
            return False 
        
        
        
    
def regenerate_pages(env):
    TEMPLATE_DIR = env.globals['design_dir']+'templates/'
    STATIC_DIR = env.globals['design_dir']+'static/'
    context = env.globals['context']
    SITE_DIR = '../sites/'+env.globals['site']+'/'
    BUILD_DIR = 'builds/'+unique_name()+'/'
    
    shutil.copytree(STATIC_DIR, SITE_DIR+BUILD_DIR) #Copy Static files from the design
    shutil.copytree(env.globals['data_dir']+'ull/', SITE_DIR+BUILD_DIR+'ull/') #Copy uploads
    for file in os.listdir(TEMPLATE_DIR):
        if not os.path.isfile(TEMPLATE_DIR+file): continue
        if 'login' in  file or 'base' in file: continue
        else:
            with open(SITE_DIR+BUILD_DIR+file, 'w') as static:
                static.write(env.get_template(file).render(isEditor=False).encode('ascii', 'xmlcharrefreplace'))
    LINK_NAME = unique_name()
    os.symlink(BUILD_DIR, SITE_DIR+LINK_NAME)
    os.rename(SITE_DIR+LINK_NAME, SITE_DIR+'current')
    builds = sorted(os.listdir(SITE_DIR+'builds/'), reverse=True)
    for build in builds[5:]:
        shutil.rmtree(SITE_DIR+'builds/'+build)
    return 'howdy'

def upload_img(env):
    extensions = ['.png', '.jpg', '.jpeg', '.gif', '.svg']
    file = request.files.get('img')
    if file:
        name, ext = os.path.splitext(file.filename.lower())
        if ext in extensions:
            path = 'ull/'+unique_name()+ext
            file.save(env.globals['data_dir']+path)
            return path
    
def random_string(len, chars="ABCDEFGHIJKLMNOPQRSTUZWXYZ"):
    return ''.join([random.choice(chars) for _ in range(len)])
def unique_name():
    return str(time.time()).replace('.','') + random_string(6)
    
def alter(env):
    context = env.globals['context']
    widget_type = request.form['type']
    
    value = json.loads(request.form['value'])
        
    new_context = dict(context.items() + [(request.form['key'], value)])
    data_dir = env.globals['data_dir']
    save_context(new_context, data_dir)
    
    if widget_type == "img": return value #Send back new url
    elif widget_type == "map": return env.get_template('widgets/map.html').render(current=value, key=request.form['key'])
    return 'yup'

def save_context(context, folder):
    unique = folder+'backups/'+unique_name()+'.json'
    backup = folder+'backups/db-'+datetime.strftime(datetime.now(), '%Y_%m_%d_%H')+'.json'
    db = folder+"db.json"
    with open(unique, 'w') as temp:
        temp.write(json.dumps(context))
    os.rename(unique, db)
    with open(unique, 'w') as temp:
        temp.write(json.dumps(context))
    os.rename(unique, backup)
    
    
# ===========================================
#
#  Utilities
#
# ===========================================
_paragraph_re = re.compile(r'(?:\r\n|\r|\n){2,}')
def nl2br(value):
    result = u'\n\n'.join(u'<p>%s</p>' % p.replace('\n', '<br \>\n') \
        for p in _paragraph_re.split(value))
    return Markup(result)
    
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
    