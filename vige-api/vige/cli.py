import os
import typer
import websockets
from vige.config import config
from vige.db import sm as sa
from sqlalchemy.orm import Session
from fastapi import Depends
import uvicorn
from vige.api.bo_user.models import BoRole, BoUser
from vige.api.constants import BoPermission
from vige.api.bo_user.security import generate_hash_password

app = typer.Typer()


@app.command("dev")
def dev_server(host: str = typer.Option("0.0.0.0", "-h", "--host",
                                        help="The interface to bind to."),
               port: int = typer.Option(5002, "-p", "--port",
                                        help="The port to bind to.")):
    """Runs a customized development server."""
    os.environ.setdefault('FASTAPI_DEBUG', '1')
    uvicorn.run("vige.app:app", host=host, port=port, reload=True)


@app.command("bo_create_user")
def bo_create_user(name: str = typer.Option(..., "-n", "--name",
                                            help="Name of the user."),
                   password: str = typer.Option(..., prompt=True,
                                                hide_input=True,
                                                confirmation_prompt=True)):
    """Create a user."""
    with sa.transaction_scope() as db:
        u = BoUser.create(db, username=name,
                          password=generate_hash_password(password))
        typer.echo(f'Created user {name}: id {u.id}')


@app.command("bo_create_role")
def bo_create_role(name: str = typer.Option(..., "-n", "--name",
                                            help="Name of the role."),
                   description: str = typer.Option(None, "-d", "--description",
                                                   help="Description of the role.")):
    """Create a role."""
    with sa.transaction_scope() as db:
        r = BoRole.create(db, name=name, description=description)
        typer.echo(f'Created role {name}: id {r.id}')


@app.command("bo_set_role")
def bo_set_role(
        user: str = typer.Option(..., "-u", "--user", help="Username."),
        role: str = typer.Option(..., "-r", "--role", help="Role name.")):
    """Set role of user."""
    with sa.transaction_scope() as db:
        r = db.query(BoRole).filter_by(name=role).first()
        if not r:
            typer.echo(f'Role "{role}" does not exist', err=True)
            raise typer.Exit(code=1)
        u = db.query(BoUser).filter_by(username=user).first()
        if not u:
            typer.echo(f'User "{user}" does not exist', err=True)
            raise typer.Exit(code=1)
        u.role = r
        typer.echo(f'Set role "{role}" to user "{user}"')


@app.command("bo_set_perm")
def bo_set_perm(
        role: str = typer.Option(..., "-r", "--role", help="Role name."),
        perm: list[str] = typer.Option(..., "-p", "--perm",
                                       help='Permissions to set. Use "all" for all permissions.')):
    """Set permissions of a role."""
    with sa.transaction_scope() as db:
        r = db.query(BoRole).filter_by(name=role).first()
        if not r:
            typer.echo(f'Role "{role}" does not exist', err=True)
            raise typer.Exit(code=1)
        perms = BoPermission.__members__.keys() if 'all' in perm else perm
        for p in perms:
            r.add_perm(p)
        typer.echo(f'Set permissions {", ".join(perms)} to role "{role}"')



if __name__ == "__main__":
    app()
