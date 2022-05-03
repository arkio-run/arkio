import os
import runpy
import sys

import click

from ..log import set_log
from ark import __version__
from ark.config import set_conf
from ark.env import set_grpc
from ark.env import set_wsgi

context_settings = {"ignore_unknown_options": True, "allow_extra_args": True}


@click.group()
@click.version_option(version=__version__)
def cli() -> None:
    pass


@cli.command(context_settings=context_settings)
@click.argument("appid", required=True)
@click.option("--level", "-l", default=0, type=int)
def create(appid: str, level: int) -> None:
    click.echo("ark create.")
    import ark.apps.creator  # noqa

    ark.apps.creator.start(appid, level)


@cli.command(context_settings=context_settings)
def shell() -> None:
    click.echo("ark shell.")
    set_log()
    set_grpc()
    set_conf()

    import ark.apps.shell  # noqa

    ark.apps.shell.start()


@cli.command(context_settings=context_settings)
@click.argument("script", required=True)
def run(script: str) -> None:
    click.echo("ark run {}".format(script))

    set_log()
    set_grpc()
    set_conf()
    runpy.run_path(script, {}, "__main__")


@cli.command(context_settings=context_settings)
@click.option("--wsgi", is_flag=True, help="running with wsgi")
def serve(wsgi: bool) -> None:
    click.echo("ark serve.")

    set_log()
    if wsgi:
        set_wsgi()
        set_conf()
        sys.argv = sys.argv[:1] + sys.argv[3:]

        import ark.apps.wsgi  # noqa

        ark.apps.wsgi.start()
    else:
        set_grpc()
        set_conf()

        import ark.apps.grpc  # noqa

        ark.apps.grpc.start()


@cli.command(context_settings=context_settings)
def worker() -> None:
    click.echo("ark worker.")
    set_log()
    set_grpc()
    set_conf()
    import ark.apps.worker  # noqa

    ark.apps.worker.start()


@cli.command(context_settings=context_settings)
def consumer() -> None:
    click.echo("ark consumer.")
    set_log()
    set_conf()

    from ark.apps.consumer import start  # noqa

    start()


@cli.command(context_settings=context_settings)
def test() -> None:
    click.echo("ark test.")
    click.echo("coming soon!\n"*3)
    set_log()


@cli.command(context_settings=context_settings)
def lint() -> None:
    click.echo("ark lint.")
    click.echo("coming soon!\n"*3)
    set_log()


def main() -> None:
    sys.path.append(os.getcwd())
    cli()
