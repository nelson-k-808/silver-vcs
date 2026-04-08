import difflib
import time
import typer
import os
import shutil
from rich.console import Console
from rich.table import Table
from silver.core.database import Database
from silver.core.index import Index
from silver.utils.paths import find_silver_root

app = typer.Typer()
console = Console()

def get_env():
    root = find_silver_root()
    if not root:
        console.print("[bold red]Fatal:[/] Not a silver repository.")
        raise typer.Exit(code=1)

    return (root, Database(os.path.join(root, ".silver", "objects")),
            Index(os.path.join(root, ".silver", "index")),
            os.path.join(root, ".silver", "HEAD"))

@app.command()
def init():
    root_dir = os.getcwd()
    silver_dir = os.path.join(root_dir, ".silver")

    if os.path.exists(silver_dir):
        console.print("[yellow]Silver repository already initialized.[/]")
        return

    os.makedirs(os.path.join(silver_dir, "objects"))
    os.makedirs(os.path.join(silver_dir, "heads"))

    with open(os.path.join(silver_dir, "HEAD"), "w") as f:
        f.write("ref: refs/heads/main")

    console.print(f"[bold green]Initialized empty Silver repository in {silver_dir}[/]")

@app.command()
def add(files: list[str]):
    root, db, index, head_path = get_env()

    for file in files:
        if os.path.exists(file):
            with open(file, "rb") as f:
                sha1 = db.store(f.read(), obj_type="blob")
            index.add(file, sha1)
            console.print(f"[green]Staged:[/] {file}")
        else:
            console.print(f"[red]Error:[/] {file} does not exist.")

@app.command()
def status():
    root, db, index, head_path = get_env()

    if not index.entries:
        console.print("Nothing staged.")
        return

    table = Table(title="Staging Area")
    table.add_column("File", style="cyan")
    table.add_column("Hash", style="magenta")

    for path, data in index.entries.items():
        table.add_row(path, data["hash"][:7])

    console.print(table)

@app.command()
def commit(message):
    root, db, index, head_path = get_env()

    if not index.entries:
        console.print("[yellow]Nothing to commit (empty index).[/]")
        return

    tree_lines = [f"100644 blob {data['hash']} {path}" for path, data in index.entries.items()]
    tree_content = "\n".join(tree_lines).encode("utf-8")
    tree_hash = db.store(tree_content, obj_type="tree")

    parent_hash = None
    if os.path.exists(head_path):
        with open(head_path, "r") as f:
            parent_hash = f.read().strip()

    commit_lines = [f"tree {tree_hash}"]
    if parent_hash:
        commit_lines.append(f"parent {parent_hash}")

    commit_lines.append(f"author Enginner <dev@example.com> {int(time.time())}")
    commit_lines.append("")
    commit_lines.append(message)

    commit_content = "\n".join(commit_lines).encode("utf-8")
    commit_hash = db.store(commit_content, obj_type="commit")

    with open(head_path, "w") as f:
        f.write(commit_hash)

    console.print(f"[bold green]Committed:[/] {commit_hash[:7]} - {message}")

@app.command()
def checkout(commit_hash: str):
    root, db, index, head_path = get_env()
    _, commit_content = db.fetch(commit_hash)
    tree_hash = commit_content.decode("utf-8").splitlines()[0].split(" ")[1]

    for item in os.listdir(root):
        if item == ".silver": continue
        path = os.path.join(root, item)
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)

    _, tree_content = db.fetch(tree_hash)
    for line in tree_content.decode("utf-8").splitlines():
        parts = line.split(" ")
        obj_hash, name = parts[2], parts[3]

        _, blob_content = db.fetch(obj_hash)
        with open(os.path.join(root, name), "wb") as f:
            f.write(blob_content)

    with open(os.path.join(root, ".silver", "HEAD"), "w") as f:
        f.write(commit_hash)

    console.print(f"[bold cyan]Switched to commit:[/] {commit_hash[:7]}")

@app.command()
def log():
    root, db, index, head_path = get_env()

    if not os.path.exists(head_path):
        console.print("[yellow]No commits yet.[/]")
        return

    with open(head_path, "r") as f:
        current_hash = f.read().strip()

    while current_hash:
        obj_type, contents = db.fetch(current_hash)
        lines = contents.decode("utf-8").splitlines()

        parent_hash = None
        author_info = ""
        message = lines[-1]
        for line in lines:
            if line.startswith("parent"):
                parent_hash = line.split(" ")[1]
            if line.startswith("author"):
                author_info = line

        console.print(f"[yellow]commit {current_hash}[/]")
        console.print(author_info)
        console.print(f"\n    {message}\n")
        current_hash = parent_hash  # Move to the previous commit

@app.command()
def diff(filename: str):
    """
    Show changes between the working directory and last commit
    """
    root, db, index, head_path = get_env()

    if not os.path.exists(head_path):
        console.print("[yellow]No commits to diff against.[/]")
        return

    with open(head_path, "r") as f:
        head_hash = f.read().strip()

    _, commit_content = db.fetch(head_hash)
    tree_hash = commit_content.decode("utf-8").splitlines()[0].split(" ")[1]

    old_blob_hash = None
    _, tree_content = db.fetch(tree_hash)

    for line in tree_content.decode("utf-8").splitlines():
        parts = line.split(" ")

        if parts[-1] == filename:
            old_blob_hash = parts[2]
            break

    if not old_blob_hash:
        console.print(f"[red]File {filename} not found in last snapshot.[/]")
        return

    _, old_raw = db.fetch(old_blob_hash)
    old_content = old_raw.decode("utf-8").splitlines()
    with open(os.path.join(root, filename), "r") as f:
        new_content = f.read().splitlines()

    diff_gen = difflib.unified_diff(
        old_content, new_content,
        fromfile=f"a/{filename}",
        tofile=f"b/{filename}",
        lineterm=""
    )

    for line in diff_gen:
        if line.startswith("+"):
            console.print(line, style="green")
        elif line.startswith("-"):
            console.print(line, style="red")
        elif line.startswith("@@"):
            console.print(line, style="cyan")
        else:
            console.print(line)

if __name__ == "__main__":
    app()