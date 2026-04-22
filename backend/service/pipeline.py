"""
AutoDBx Pipeline Runner
------------------------
Executes each Databricks bundle step as a subprocess,
streams output line-by-line to the WebSocket room,
and updates the migration DB record at each step transition.
"""

import asyncio
import os
import subprocess
from uuid import UUID

from core.database import SessionLocal
from fastapi import HTTPException
from model.migration import MigrationStatus
from schema.migration import MigrationStepUpdate
from service import migration as migration_svc
from sqlalchemy.orm import Session
from websocket.manager import manager

AUTO_DBX_ROOT = os.getenv("AUTO_DBX_ROOT")
if not AUTO_DBX_ROOT:
    AUTO_DBX_ROOT = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "AutoDBx")
    )

STEPS = [
    {
        "key": "validate",
        "label": "Validate Bundle",
        "command": "databricks bundle validate",
        "update_fn": migration_svc.update_validate_step,
    },
    {
        "key": "deploy",
        "label": "Deploy Bundle",
        "command": "databricks bundle deploy",
        "update_fn": migration_svc.update_deploy_step,
    },
    {
        "key": "config_table",
        "label": "Config Table Creation",
        "command": "databricks bundle run config_table_creation",
        "update_fn": migration_svc.update_config_table_step,
    },
    {
        "key": "migration_job",
        "label": "Migration Job",
        "command": "databricks bundle run migration_job",
        "update_fn": migration_svc.update_migration_job_step,
    },
]


def get_project_working_dir(project_name: str) -> str:
    """
    Constructs the absolute path to the specified AutoDBx project directory.
    Uses the AUTO_DBX_ROOT environment variable (default: /app/AutoDBx).
    """
    project_path = os.path.join(AUTO_DBX_ROOT, project_name)

    if not os.path.isdir(project_path):
        raise HTTPException(
            status_code=404, detail=f"Project directory not found: {project_path}."
        )
    return project_path


async def _stream_process(
    migration_id: UUID,
    step_key: str,
    command: str,
    cwd: str,
) -> tuple[int, list[str]]:
    """
    Run a subprocess and stream each output line to the WS room.
    Returns (exit_code, all_output_lines).
    """
    process = await asyncio.create_subprocess_shell(
        command,
        cwd=cwd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )

    output_lines: list[str] = []

    async for raw_line in process.stdout:
        line = raw_line.decode(errors="replace").rstrip()
        output_lines.append(line)
        await manager.send_log(migration_id, step=step_key, log=line)

    await process.wait()
    exit_code = process.returncode

    await manager.send_log(
        migration_id,
        step=step_key,
        log=f"[Process exited with code {exit_code}]",
        exit_code=exit_code,
    )
    return exit_code, output_lines


async def run_step(
    migration_id: UUID,
    step_key: str,
    project_dir: str,
) -> None:
    """
    Execute a single pipeline step.
    Streams live output through the WebSocket room and persists
    step status + metadata after completion.
    """
    with SessionLocal() as db:
        # Find the step configuration
        step = next((s for s in STEPS if s["key"] == step_key), None)
        if not step:
            await manager.send_error(
                migration_id, step_key, f"Invalid step key: {step_key}"
            )
            return

        label: str = step["label"]
        command: str = step["command"]
        update_fn = step["update_fn"]

        # --- Mark step as RUNNING ---
        await manager.send_step_status(migration_id, step_key, "running")
        update_fn(
            db,
            migration_id,
            MigrationStepUpdate(status=MigrationStatus.RUNNING),
        )

        # --- Run the subprocess and stream output ---
        try:
            exit_code, lines = await _stream_process(
                migration_id, step_key, command, cwd=project_dir
            )
        except Exception as exc:
            await manager.send_error(migration_id, step_key, str(exc))
            update_fn(
                db,
                migration_id,
                MigrationStepUpdate(
                    status=MigrationStatus.FAILED,
                    meta_data={"error": str(exc)},
                ),
            )
            return

        # --- Persist result ---
        final_status = (
            MigrationStatus.SUCCESS if exit_code == 0 else MigrationStatus.FAILED
        )
        update_fn(
            db,
            migration_id,
            MigrationStepUpdate(
                status=final_status,
                meta_data={"exit_code": exit_code, "output": "\n".join(lines[-50:])},
            ),
        )
        await manager.send_step_status(migration_id, step_key, final_status.value)
