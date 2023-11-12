import os
import logging
from src.config import *
import random
import shutil

def get_all_files_in(path):
    file_paths = []
    for root, dirs, files in os.walk(path):
        for file in files:
            file_paths.append(os.path.join(root, file))
    return file_paths


def setup_logging(log_file):
    # Create a logger object
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.ERROR)

    # Create file handler which logs error messages
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.ERROR)

    # Create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)

    # Add the handlers to the logger
    logger.addHandler(fh)
    
    return logger

def sample_and_copy_files(source_dir, dest_dir, sample_fraction=0.05):
    # Get a list of files in the source directory
    files = [f for f in os.listdir(source_dir) if os.path.isfile(os.path.join(source_dir, f))]

    # Calculate the number of files to sample (10% of the total files)
    sample_size = int(len(files) * sample_fraction)

    # Randomly select the files
    sampled_files = random.sample(files, sample_size)

    # Copy the sampled files to the destination directory
    for file in sampled_files:
        source_file = os.path.join(source_dir, file)
        destination_file = os.path.join(dest_dir, file)
        shutil.copy2(source_file, destination_file)
        print(f"Copied {file} to {dest_dir}")