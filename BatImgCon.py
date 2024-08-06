"""
A simple to use Python tool to batch convert images between formats, including AVIF.
"""
# Batch Image Converter (BatImgCon) v1.0.0

# TODO
# - Linux & MacOS support for priorities

import os
import glob
import sys
import signal
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import pillow_avif
import typer
import win32api
import win32process
from PIL import Image
from rich import print as richprint

# Flag to indicate if the script should be interrupted
interrupted = False
def signal_handler(sig, frame):
    """
    Handles the interrupt signal
    """
    global interrupted
    richprint("\n[bold red]Interrupt received, stopping ASAP.[/bold red]\n")
    interrupted = True

# Register the signal handler
signal.signal(signal.SIGINT, signal_handler)

def reduce_prio():
    """
    Reduces process priority to make background processing more pleasant
    """
    if sys.platform == "win32":
        try:
            win32process.SetPriorityClass(
                win32api.GetCurrentProcess(),
                win32process.BELOW_NORMAL_PRIORITY_CLASS
            )
            richprint("Process priority reduced successfully to 'Below Normal'")
        except Exception as error:
            richprint(f"Failed to reduce process priority: {error}")
    else:
        richprint("Unsupported operating system, process priority not reduced")

def convert_file(file: str, output_dir: str, input_format: str, output_format: str) -> bool:
    """
    Converts a file to a different format and saves it in a different directory
    """
    if interrupted:
        return False  # Exit early if interrupted
    try:
        image = Image.open(file)
        output_path = os.path.join(
            output_dir,
            os.path.basename(file).replace(f".{input_format}",f".{output_format}")
        )
        image.save(output_path, format=output_format)
        richprint(f"Converted {file} to {output_path}")
        return True
    except Exception as e:
        richprint(f"Failed to convert {file}: {e}")
        return False
    finally:
        image.close()

def main(input_dir: str, input_format: str,
         output_dir: str, output_format: str,
         workers_count: int = os.cpu_count(), reduced_prio: bool = True):
    """
    Converts all images of INPUT_FORMAT inside INPUT_DIR to OUTPUT_FORMAT inside OUTPUT_DIR

    Example: D:\\Screenshots png      D:\\Screenshots_AVIF avif

    All PNG images here ^  to AVIF images in there ^

    --workers-count will default to your CPU core count.

    --reduced-prio reduces the process priority of the task, to make background processing more pleasant.
    """

    # Verify that the paths don't end in slash
    if input_dir[-1] in ['/', '\\']:
        input_dir = input_dir[0:-1]
    if output_dir[-1] in ['/', '\\']:
        output_dir = output_dir[0:-1]

    if not os.path.isdir(input_dir):
        richprint("Failed to find input directory! Verify that your arguments are correct")
        sys.exit()

    # Create the output directory if it doesn't exist
    if not os.path.isdir(output_dir):
        try:
            richprint(f"Creating output directory: {output_dir}")
            os.mkdir(output_dir)
        except Exception as e:
            richprint(f"Failed to create output directory: {e}")
            sys.exit()

    # Reduce prio
    if reduced_prio:
        reduce_prio()

    richprint(f"Starting conversion from [bold]{input_dir} to {output_dir}[/bold]\n")

    # Get list of PNG files
    files = glob.glob(input_dir + f"/*.{input_format}")

    start_time = time.time()
    successful_conversions = 0
    try:
        with ThreadPoolExecutor(max_workers=workers_count) as executor:
            futures = {executor.submit(convert_file, file, output_dir, input_format, output_format): file for file in files}
            for future in as_completed(futures):
                if future.result():
                    successful_conversions += 1
                if interrupted:
                    executor.shutdown()
    except Exception as e:
        richprint(f"An error occurred: {e}")

    richprint(f"[green]Successfully converted [bold]{successful_conversions} out of {len(files)}[/bold] files.[green]")
    richprint(f"Execution time: {round(time.time() - start_time)}s")

if __name__ == "__main__":
    richprint("Welcome to Batch Image Converter (BatImgCon) version 1.0.0")
    typer.run(main)
