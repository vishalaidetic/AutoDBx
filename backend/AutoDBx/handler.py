import os
import shutil
import subprocess

from dotenv import load_dotenv
from fastapi import HTTPException
from fastapi.responses import StreamingResponse

load_dotenv()

REPOSITORY_URL = os.getenv("REPOSITORY_URL")
# WORKING_DIR = None  # global repo path after clone


def run_command(command: str, cwd: str = None) -> dict:
    """
    Run a shell command and return stdout, stderr, returncode.
    """
    try:
        result = subprocess.run(
            command, cwd=cwd, check=True, capture_output=True, text=True, shell=True
        )
        return {
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "returncode": result.returncode,
        }
    except subprocess.CalledProcessError as e:
        return {
            "stdout": e.stdout.strip() if e.stdout else "",
            "stderr": e.stderr.strip() if e.stderr else "",
            "returncode": e.returncode,
        }


# def clone_and_cd_repository(repo_url: str, base_dir: str = "/tmp", branch: str | None = None) -> str:
#     """
#     Clones a git repository into a specified base directory and then
#     changes the current working directory to the cloned repository.
#     Sets the global WORKING_DIR to the 'mongodb' subdirectory.
#
#     Args:
#         repo_url: The URL of the git repository to clone.
#         base_dir: The base directory where the repository will be cloned.
#         branch: Optional. The name of the branch to clone. If None, the default branch is cloned.
#
#     Returns:
#         A message indicating success and the working directory.
#
#     Raises:
#         RuntimeError: If cloning fails or the expected subdirectory is not found.
#     """
#     global WORKING_DIR
#     repo_name = repo_url.split("/")[-1].replace(".git", "")
#     destination_path = os.path.join(base_dir, repo_name)
#
#     # Clean up if directory already exists to ensure a fresh clone
#     if os.path.exists(destination_path):
#         shutil.rmtree(destination_path)
#
#     try:
#         git_command = ["git", "clone"]
#         if branch:
#             git_command.extend(["--branch", branch])
#         git_command.extend([repo_url, destination_path])
#
#         # Clone the repository
#         process = subprocess.run(
#             git_command, # Use the constructed git command
#             cwd=base_dir, # Run git clone from base_dir
#             check=True, # Raise CalledProcessError for non-zero exit codes
#             capture_output=True,
#             text=True
#         )
#         print(f"Git clone stdout: {process.stdout}")
#         print(f"Git clone stderr: {process.stderr}")
#     except subprocess.CalledProcessError as e:
#         raise RuntimeError(f"Error cloning repository (branch '{branch or 'default'}'): {e.stderr.strip() or 'Unknown git error'}")
#     except Exception as e:
#         raise RuntimeError(f"An unexpected error occurred during cloning: {e}")
#
#     # Set working directory to the 'mongodb' subdirectory
#     # Check for the common "AutoDBx_upd/mongodb" first, then fallback to "mongodb"
#     potential_working_dirs = [
#         os.path.join(destination_path, "AutoDBx_upd", "mongodb"),
#         os.path.join(destination_path, "mongodb")
#     ]
#     found_working_dir = None
#     for p_dir in potential_working_dirs:
#         if os.path.exists(p_dir):
#             found_working_dir = p_dir
#             break
#
#     if found_working_dir:
#         WORKING_DIR = found_working_dir
#     else:
#         raise RuntimeError(f"Expected Databricks bundle directory not found in any of: {', '.join(potential_working_dirs)}. "
#                            f"Check repository structure relative to clone root '{destination_path}'.")
#
#     return f"Cloned successfully. Working dir: {WORKING_DIR}"


def get_project_working_dir(project_name: str) -> str:
    """
    Constructs the absolute path to the specified AutoDBx project directory.
    """
    # Assuming the backend is run from within the 'backend' directory
    # os.path.abspath(os.path.join(os.getcwd(), os.pardir)) goes up one level to Data_Visualization
    # then os.path.join(..., "AutoDBx", project_name) goes into the specific project folder
    autodbx_path = os.path.abspath(
        os.path.join(os.getcwd(), os.pardir, "AutoDBx", project_name)
    )
    print("Vishal", autodbx_path)

    if not os.path.isdir(autodbx_path):
        raise HTTPException(
            status_code=400,
            detail=f"Project directory not found: {autodbx_path}. "
            f"Please ensure '{project_name}' exists under Data_Visualization/AutoDBx.",
        )
    return autodbx_path


def stream_command(command: str, cwd: str = None):
    """
    Generator that yields command output line by line.
    """
    process = subprocess.Popen(
        command,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        shell=True,
        bufsize=1,
    )

    for line in iter(process.stdout.readline, ""):
        yield line

    process.stdout.close()
    process.wait()
    yield f"\n[Process finished with exit code {process.returncode}]\n"


def databricks_validate(project_name: str) -> StreamingResponse:
    # if not WORKING_DIR:
    #     raise HTTPException(status_code=400, detail="Repository not cloned yet. Please clone the repository first.")
    working_dir = get_project_working_dir(project_name)
    return StreamingResponse(
        stream_command("databricks bundle validate", cwd=working_dir),
        media_type="text/plain",
    )


def databricks_deploy(project_name: str) -> StreamingResponse:
    # if not WORKING_DIR:
    #     raise HTTPException(status_code=400, detail="Repository not cloned yet. Please clone the repository first.")
    working_dir = get_project_working_dir(project_name)
    return StreamingResponse(
        stream_command("databricks bundle deploy", cwd=working_dir),
        media_type="text/plain",
    )


def databricks_run_config_table_creation(project_name: str) -> StreamingResponse:
    # if not WORKING_DIR:
    #     raise HTTPException(status_code=400, detail="Repository not cloned yet. Please clone the repository first.")
    working_dir = get_project_working_dir(project_name)
    return StreamingResponse(
        stream_command("databricks bundle run config_table_creation", cwd=working_dir),
        media_type="text/plain",
    )


def databricks_run_migration_job(project_name: str) -> StreamingResponse:
    # if not WORKING_DIR:
    #     raise HTTPException(status_code=400, detail="Repository not cloned yet. Please clone the repository first.")
    working_dir = get_project_working_dir(project_name)
    return StreamingResponse(
        stream_command("databricks bundle run migration_job", cwd=working_dir),
        media_type="text/plain",
    )
