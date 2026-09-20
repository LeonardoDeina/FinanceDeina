from fastapi import APIRouter, HTTPException

from app.backup.service import BackupError, create_backup, list_backups, restore_backup

router = APIRouter(prefix="/backup", tags=["backup"])


@router.post("", status_code=201)
def trigger_backup():
    try:
        path = create_backup()
    except BackupError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"filename": path.name}


@router.get("")
def get_backups():
    return {"backups": [p.name for p in list_backups()]}


@router.post("/{filename}/restore")
def trigger_restore(filename: str, confirm: bool = False):
    if not confirm:
        raise HTTPException(status_code=400, detail="Confirme a restauração com confirm=true; isso substitui os dados atuais.")
    try:
        restore_backup(filename)
    except BackupError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"status": "restored", "filename": filename}
