import uuid
from pathlib import Path

import matplotlib
import pandas as pd

matplotlib.use("Agg")  # Use Agg backend for non-interactive environments
import matplotlib.pyplot as plt


def plot_pandas_series_line_graph(
    series: pd.Series, title: str = "Line Plot", xlabel: str = "Index", ylabel: str = "Value", output_dir: str = "plots"
) -> str:
    """Plots a line graph from a pandas Series and saves it as an image file.

    The function generates a line plot, saves it to the specified directory
    with a unique filename, and returns the absolute path to the saved image.

    Args:
        series: A pandas Series containing the data to plot.
        title: The title of the plot. Defaults to "Line Plot".
        xlabel: The label for the x-axis. Defaults to "Index".
        ylabel: The label for the y-axis. Defaults to "Value".
        output_dir: The directory where the plot image will be saved.
                      Defaults to "plots". Created if it doesn't exist.

    Returns:
        The absolute path to the saved plot image (e.g., "/path/to/plots/plot_uuid.png").
        Returns an error message string if plotting fails.
    """
    try:
        if not isinstance(series, pd.Series):
            return "Error: Input data must be a pandas Series."
        if series.empty:
            return "Error: Input pandas Series is empty."

        Path(output_dir).mkdir(parents=True, exist_ok=True)

        fig, ax = plt.subplots()
        series.plot(kind="line", ax=ax)
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        plt.tight_layout()

        filename = f"plot_{uuid.uuid4().hex}.png"
        filepath = Path(output_dir) / filename

        plt.savefig(filepath)
        plt.close(fig)  # Close the figure to free memory

        return str(Path(filepath).resolve())
    except Exception as e:
        return f"An error occurred during plotting: {e}"
