from pathlib import Path
from uuid import uuid4

from app.services.storage.base import StorageService


class LocalStorageService(StorageService):
    def __init__(
        self,
        upload_dir: str = "uploads",
    ):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

    async def save(
        self,
        filename: str,
        content: bytes,
    ) -> str:

        path = self.upload_dir / filename

        path.write_bytes(content)

        return str(path)

    async def read(
        self,
        path: str,
    ) -> bytes:

        return Path(path).read_bytes()

    async def upload(
        self,
        *,
        filename: str,
        content: bytes,
    ) -> str:
        suffix = Path(filename).suffix

        storage_key = f"{uuid4()}{suffix}"

        path = self.upload_dir / storage_key

        path.write_bytes(content)

        return storage_key

    async def download(
        self,
        storage_key: str,
    ) -> bytes:
        path = self.upload_dir / storage_key

        return path.read_bytes()

    async def delete(
        self,
        storage_key: str,
    ) -> None:
        path = self.upload_dir / storage_key

        if path.exists():
            path.unlink()

    async def exists(
        self,
        storage_key: str,
    ) -> bool:
        return (self.upload_dir / storage_key).exists()