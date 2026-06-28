from pathlib import Path
import nbformat
from nbclient import NotebookClient


project_dir = Path(__file__).resolve().parent
notebooks = sorted(project_dir.glob("*.ipynb"))

for notebook_path in notebooks:
    print(f"Running {notebook_path.name}...")
    notebook = nbformat.read(notebook_path, as_version=4)
    client = NotebookClient(notebook, timeout=300, kernel_name="python3")
    client.execute()
    nbformat.write(notebook, notebook_path)
    print(f"Done {notebook_path.name}")

print("All notebooks executed successfully.")
