from jinja2 import Environment, FileSystemLoader

class HappyEnv(Environment):
    def __init__(self, path):
        Environment.__init__(self, loader=FileSystemLoader(path))
        
    def render(self, template, **kwargs):
        return self.get_template(template).render(**kwargs)
        