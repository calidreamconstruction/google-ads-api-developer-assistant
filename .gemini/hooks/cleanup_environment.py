# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
# CRITICAL MAINTENANCE NOTE - DO NOT REMOVE
# ==============================================================================
# ⚠️ DO NOT migrate lifecycle hooks (SessionStart/SessionEnd) to the extension
# manifest (hooks/hooks.json or gemini-extension.json).
#
# Doing so breaks hook execution in the OSS version of gemini-cli used in this
# workspace. Hooks MUST remain registered in `.gemini/settings.json` using the
# `matcher` wrapper list structure to function correctly.
# ==============================================================================

import os
import shutil
import sys

def cleanup():
    # Determine paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # .gemini/hooks/ -> project root is 2 levels up
    project_root = os.path.abspath(os.path.join(script_dir, "../.."))
    config_dir = os.path.join(project_root, "config")

    if not os.path.exists(config_dir):
        print(f"Config directory {config_dir} does not exist. Nothing to clean.", file=sys.stderr)
        return

    try:
        # User requested to remove *all files* in the config directory.
        # We could also remove the directory itself. Let's remove content.
        for filename in os.listdir(config_dir):
            if filename == ".gitkeep":
                continue
            file_path = os.path.join(config_dir, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f"Failed to delete {file_path}. Reason: {e}", file=sys.stderr)
        
        # Delete isolated virtual environment
        venv_dir = os.path.join(project_root, ".venv")
        if os.path.exists(venv_dir):
            print(f"Deleting virtual environment at {venv_dir}...", file=sys.stderr)
            try:
                shutil.rmtree(venv_dir)
                print("Virtual environment deleted successfully.", file=sys.stderr)
            except Exception as e:
                print(f"Failed to delete virtual environment: {e}", file=sys.stderr)


    except Exception as e:
        print(f"Error cleaning up config directory: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    cleanup()
