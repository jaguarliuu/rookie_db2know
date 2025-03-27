from pathlib import Path
from jinja2 import Environment, FileSystemLoader, TemplateNotFound

class PromptLoader:
    def __init__(self):
        self.env = Environment(
            loader=FileSystemLoader(Path(__file__).parent.parent / 'prompt'),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
    def get_prompt(
            self, 
            context: dict
    ) -> str:
        try:
            template = self.env.get_template(f"metadata_know.jinja")
        except TemplateNotFound:
            template = self.env.get_template("base_prompt.jinja")
        return template.render(context)
        