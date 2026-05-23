import os
import json
from typing import List
from pathlib import Path

from app.tool_registry import ToolDefinition
from app.utils.logger import logger

try:
    import yaml
except ImportError:
    yaml = None

def load_plugins_from_directory(directory_path: str) -> List[ToolDefinition]:
    """
    Scans a folder for plugin manifests (JSON or YAML), validates them,
    and returns a list of ToolDefinition objects.
    """
    plugins = []
    path = Path(directory_path)
    
    if not path.exists() or not path.is_dir():
        logger.warning(f"[PLUGIN LOADER] Directory not found: {directory_path}")
        return plugins
        
    for file_path in path.iterdir():
        if not file_path.is_file():
            continue
            
        ext = file_path.suffix.lower()
        if ext not in [".json", ".yaml", ".yml"]:
            continue
            
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                if ext == ".json":
                    manifest = json.load(f)
                else:
                    if yaml is None:
                        logger.error("[PLUGIN LOADER] PyYAML is required to load YAML plugins.")
                        continue
                    manifest = yaml.safe_load(f)
            
            # Basic validation
            required_fields = ["name", "description", "input_schema", "endpoint"]
            missing = [field for field in required_fields if field not in manifest]
            if missing:
                logger.error(f"[PLUGIN LOADER] Plugin {file_path.name} is missing required fields: {missing}")
                continue
                
            # Validate schema correctness
            if not isinstance(manifest["input_schema"], dict):
                logger.error(f"[PLUGIN LOADER] Plugin {file_path.name} has invalid input_schema format (must be dict)")
                continue
                
            # Validate endpoint format
            endpoint = manifest["endpoint"]
            if not isinstance(endpoint, str) or not (endpoint.startswith("/") or endpoint.startswith("http")):
                logger.error(f"[PLUGIN LOADER] Plugin {file_path.name} has invalid endpoint format: {endpoint}")
                continue
                
            # Normalize into internal ToolDefinition
            # We treat auth_type differently as ToolDefinition expects requires_user_id
            requires_user_id = manifest.get("requires_user_id", True)
            if "auth_type" in manifest and manifest["auth_type"] == "none":
                requires_user_id = False
                
            tool_def = ToolDefinition(
                name=manifest["name"],
                description=manifest["description"],
                input_schema=manifest["input_schema"],
                endpoint=manifest["endpoint"],
                http_method=manifest.get("http_method", "GET"),
                requires_user_id=requires_user_id,
                tags=manifest.get("tags", []),
                path_param=manifest.get("path_param")
            )
            plugins.append(tool_def)
            logger.info(f"[PLUGIN LOADER] Successfully loaded plugin: {tool_def.name}")
            
        except Exception as e:
            logger.error(f"[PLUGIN LOADER] Failed to load plugin {file_path.name}: {e}")
            
    return plugins
