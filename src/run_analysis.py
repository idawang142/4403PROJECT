"""Execute the report notebook without a notebook server or kernel launcher."""
import io
import os
import sys
from pathlib import Path


def main():
    for name in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
        os.environ.setdefault(name, "1")
    import nbformat
    from IPython.core.interactiveshell import InteractiveShell
    from IPython.display import Image, display
    from IPython.utils.capture import capture_output
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    root = Path(__file__).resolve().parents[1]
    os.chdir(root)
    sys.path.insert(0, str(root))

    def show_figures(*args, **kwargs):
        for number in plt.get_fignums():
            buffer = io.BytesIO()
            plt.figure(number).savefig(buffer, format="png", dpi=110,
                                       bbox_inches="tight")
            display(Image(data=buffer.getvalue()))

    plt.show = show_figures
    shell = InteractiveShell.instance()
    path = root / "notebooks" / "04_analysis.ipynb"
    notebook = nbformat.read(path, as_version=4)
    count = 0
    for index, cell in enumerate(notebook.cells):
        if cell.cell_type != "code":
            continue
        count += 1
        print(f"Executing analysis cell {index}", flush=True)
        with capture_output() as captured:
            result = shell.run_cell(cell.source, store_history=True)
        if result.error_before_exec or result.error_in_exec:
            print(captured.stdout, captured.stderr)
            raise result.error_before_exec or result.error_in_exec
        cell.execution_count = count
        cell.outputs = []
        for name, text in (("stdout", captured.stdout), ("stderr", captured.stderr)):
            if text:
                cell.outputs.append(nbformat.v4.new_output("stream", name=name,
                                                           text=text))
        for output in captured.outputs:
            cell.outputs.append(nbformat.v4.new_output("display_data", data=output.data,
                                                       metadata=output.metadata))
        plt.close("all")
    nbformat.validate(notebook)
    nbformat.write(notebook, path)
    print(f"Saved {count} executed analysis cells, figures and summaries.", flush=True)


if __name__ == "__main__":
    main()
