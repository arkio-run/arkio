import os

from jinja2 import Environment
from jinja2 import FileSystemLoader


def gen(appid, project_dir, sub_template_dir):
    name = appid.split(".")[-1]

    abspath = os.path.join(os.path.dirname(__file__), "../conf/templates/{}/".format(sub_template_dir))
    template_dir = os.path.realpath(abspath)

    prefix_length = len(template_dir) + 1
    engine = Environment(loader=FileSystemLoader(template_dir))
    for root, dirs, files in os.walk(template_dir):
        source_dir = root[prefix_length:]
        target_dir = os.path.join(project_dir, source_dir.format(name=name))

        if target_dir:
            os.makedirs(target_dir, exist_ok=True)

        for fn in files:
            tpl = os.path.join(source_dir, fn)
            content = engine.get_template(tpl).render(name=name, appid=appid)

            fp = os.path.join(project_dir, target_dir, fn).replace(".jinja", "")
            with open(fp, "w", encoding="utf-8") as f:
                f.write(content + "\n")


def start(appid: str, level: int) -> None:
    name = appid.split(".")[-1]
    project_dir = os.path.join(os.getcwd(), name)

    if os.path.exists(project_dir):
        print(f"{project_dir} already exists")
        return

    gen(appid, project_dir, "commons")
    gen(appid, project_dir, "v{}".format(level))
