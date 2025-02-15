import hashlib

import rich
import typer


def encrypt_flag():
    """
    Encrypt flag via sha256 mand give it back to user.
    Don't input whole flags, only their inner strings.
    For example:
    Not "hack4krak('skibidi')" but just "skibidi".
    """
    while True:
        flag = typer.prompt("Input flag to encrypt")
        flag_retype = typer.prompt("Retype flag to confirm")
        if flag != flag_retype:
            rich.print("\n[red]Inputs are not the same\n")
        else:
            encrypted_flag = hashlib.sha256(flag.encode("utf-8"))
            print(encrypted_flag.hexdigest())
            break
