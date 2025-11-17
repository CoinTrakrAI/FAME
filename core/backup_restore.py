#!/usr/bin/env python3
"""
FAME Backup/Restore System
Creates backups before self-evolution and allows restoration
"""

import shutil
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

BACKUP_DIR = Path(__file__).parent.parent / "backups"
BACKUP_DIR.mkdir(exist_ok=True)

BACKUP_MANIFEST = BACKUP_DIR / "backup_manifest.json"

# Files that should be backed up before self-evolution
FILES_TO_BACKUP = [
    "core/self_evolution.py",
    "core/universal_developer.py",
    "core/universal_hacker.py",
    "core/book_reader.py",
    "core/assistant/nlu.py",
    "core/assistant/dialog_manager.py",
    "orchestrator/brain.py",
    "fame_chat_ui.py",
]


def create_backup(backup_name: Optional[str] = None) -> str:
    """
    Create a backup of critical files before self-evolution
    
    Returns:
        backup_id: Unique identifier for this backup
    """
    if backup_name is None:
        backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    backup_id = backup_name
    backup_path = BACKUP_DIR / backup_id
    backup_path.mkdir(exist_ok=True)
    
    project_root = Path(__file__).parent.parent
    backed_up_files = []
    
    for file_pattern in FILES_TO_BACKUP:
        file_path = project_root / file_pattern
        if file_path.exists():
            # Create directory structure in backup
            backup_file_path = backup_path / file_pattern
            backup_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy file
            shutil.copy2(file_path, backup_file_path)
            backed_up_files.append(file_pattern)
            logger.info(f"Backed up: {file_pattern}")
    
    # Save backup manifest
    manifest = load_manifest()
    manifest[backup_id] = {
        "timestamp": datetime.now().isoformat(),
        "files": backed_up_files,
        "description": f"Pre-evolution backup created automatically"
    }
    save_manifest(manifest)
    
    logger.info(f"Backup created: {backup_id} with {len(backed_up_files)} files")
    return backup_id


def load_manifest() -> Dict:
    """Load backup manifest"""
    if BACKUP_MANIFEST.exists():
        try:
            with open(BACKUP_MANIFEST, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading manifest: {e}")
            return {}
    return {}


def save_manifest(manifest: Dict):
    """Save backup manifest"""
    with open(BACKUP_MANIFEST, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)


def list_backups() -> List[Dict]:
    """List all available backups"""
    manifest = load_manifest()
    backups = []
    for backup_id, info in manifest.items():
        backups.append({
            "id": backup_id,
            "timestamp": info.get("timestamp"),
            "files_count": len(info.get("files", [])),
            "description": info.get("description", "")
        })
    return sorted(backups, key=lambda x: x["timestamp"], reverse=True)


def restore_backup(backup_id: str, dry_run: bool = False) -> bool:
    """
    Restore files from a backup
    
    Args:
        backup_id: ID of backup to restore
        dry_run: If True, only show what would be restored
    
    Returns:
        True if successful
    """
    manifest = load_manifest()
    if backup_id not in manifest:
        logger.error(f"Backup {backup_id} not found")
        return False
    
    backup_path = BACKUP_DIR / backup_id
    if not backup_path.exists():
        logger.error(f"Backup directory not found: {backup_path}")
        return False
    
    project_root = Path(__file__).parent.parent
    files_restored = []
    
    for file_pattern in manifest[backup_id]["files"]:
        backup_file = backup_path / file_pattern
        target_file = project_root / file_pattern
        
        if backup_file.exists():
            if dry_run:
                logger.info(f"Would restore: {file_pattern}")
            else:
                # Create backup of current file before restoring
                if target_file.exists():
                    current_backup = target_file.with_suffix(target_file.suffix + ".pre_restore")
                    shutil.copy2(target_file, current_backup)
                
                # Restore file
                target_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(backup_file, target_file)
                files_restored.append(file_pattern)
                logger.info(f"Restored: {file_pattern}")
    
    if not dry_run:
        logger.info(f"Restored {len(files_restored)} files from backup {backup_id}")
    
    return len(files_restored) > 0


def restore_latest_backup(dry_run: bool = False) -> bool:
    """Restore the most recent backup"""
    backups = list_backups()
    if not backups:
        logger.error("No backups available")
        return False
    
    latest = backups[0]
    return restore_backup(latest["id"], dry_run=dry_run)


if __name__ == "__main__":
    # Test backup/restore
    print("Creating test backup...")
    backup_id = create_backup("test_backup")
    print(f"Created backup: {backup_id}")
    
    print("\nAvailable backups:")
    for backup in list_backups():
        print(f"  - {backup['id']} ({backup['timestamp']})")

