import hashlib

import rich
import typer


def hash_flag():
    """
    This function prompts the user to input a flag, confirms it, and then hashes it.
    Do not include the full flag format (e.g., exclude hack4KrakCTF{}), only hash the part inside the braces.
    """
    while True:
        flag = typer.prompt("Input flag to hash")
        flag_retype = typer.prompt("Retype flag to confirm")

        if flag != flag_retype:
            rich.print("\n[red]Inputs are not the same\n")
            continue

        if any(char in flag for char in "{}"):
            rich.print("\n[yellow]Warning: Please submit only the inner flag string without curly braces.")
            rich.print("[yellow]Warning: For example, use 'skibidi' instead of 'hack4KrakCTF{skibidi}'.")
            rich.print("[yellow]Warning: Repeat the command with the corrected flag.\n")

        hashed_flag = hashlib.sha256(flag.encode("utf-8"))
        print(hashed_flag.hexdigest())
        break
