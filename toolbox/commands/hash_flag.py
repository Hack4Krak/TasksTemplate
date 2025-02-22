import hashlib

import rich
import typer


def hash_flag():
    """
    Hash flag via sha256 and give it back to user.
    Don't input whole flags, only their inner strings.
    For example:
    Not "hack4KrakCTF('skibidi')" but just "skibidi".
    """
    while True:
        flag = typer.prompt("Input flag to hash")
        flag_retype = typer.prompt("Retype flag to confirm")
        if flag != flag_retype:
            rich.print("\n[red]Inputs are not the same\n")
        else:
            hashed_flag = hashlib.sha256(flag.encode("utf-8"))
            print(hashed_flag.hexdigest())
            break
