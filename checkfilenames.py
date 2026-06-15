"""Keep the dataset sub-folders in sync by file stem.

A part is only usable if it exists in every modality, so this script keeps only
the parts whose stem (file name without extension) is present in all four
folders -- Graph, Label, STEP and PMI -- and deletes any orphaned files that
appear in some folders but not the others.
"""
from pathlib import Path

def list_file_stems(directory):
    """Returns a set of file stems for all files in the given directory."""
    return {file.stem for file in directory.iterdir() if file.is_file()}

def delete_files_not_in_all_dirs(directory, common_stems):
    """Deletes files in the directory whose stems are not in common_stems."""
    for file in directory.iterdir():
        if file.stem not in common_stems and file.is_file():
            file.unlink()
            print(f"Deleted {file}")

path = Path(__file__).resolve().parent / "data"

# Directories
graph_dir  = Path(path, "Graph")
labels_dir = Path(path, "Label")
step_dir   = Path(path, "STEP")
pmi_dir    = Path(path, "PMI")

# Get the stems for each directory
graph_stems  = list_file_stems(graph_dir)
labels_stems = list_file_stems(labels_dir)
step_stems   = list_file_stems(step_dir)
pmi_stems    = list_file_stems(pmi_dir)

# Find common stems
common_stems = graph_stems & labels_stems & step_stems & pmi_stems

# Delete files whose stems are not in the set of common stems
delete_files_not_in_all_dirs(graph_dir, common_stems)
delete_files_not_in_all_dirs(labels_dir, common_stems)
delete_files_not_in_all_dirs(step_dir, common_stems)
delete_files_not_in_all_dirs(pmi_dir, common_stems)

print("Cleanup of files not present in all directories complete.")

