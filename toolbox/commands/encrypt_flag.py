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
    are_flags_same = False
    while not are_flags_same:
        flag = typer.prompt("Input flag to encrypt")
        flag_retype = typer.prompt("Retype flag")
        if flag != flag_retype:
            rich.print("\n[red]Inputs are not the same\n")
            continue
        are_flags_same = True
    else:
        encrypted_flag = hashlib.sha256(flag.encode('utf-8'))
        print(encrypted_flag.hexdigest())
