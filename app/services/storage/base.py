from abc import ABC, abstractmethod


class StorageService(ABC):
    """
    Abstract storage backend.

    Can be implemented by:
    - Local filesystem
    - Amazon S3
    - MinIO
    - Azure Blob
    - Google Cloud Storage
    """

    @abstractmethod
    async def save(
        self,
        filename: str,
        content: bytes,
    ) -> str:
        """
        Persist a file and return its storage path or key.

        Examples:
        - Local: uploads/abc123.pdf
        - S3: documents/abc123.pdf
        """
        raise NotImplementedError

    @abstractmethod
    async def read(
        self,
        path: str,
    ) -> bytes:
        """
        Read a stored file and return its bytes.

        Args:
            path: Storage path or object key returned by save().

        Returns:
            Raw file bytes.
        """
        raise NotImplementedError

    @abstractmethod
    async def upload(
        self,
        *,
        filename: str,
        content: bytes,
    ) -> str:
        """
        Store file.

        Returns storage key.
        """
        raise NotImplementedError

    @abstractmethod
    async def download(
        self,
        storage_key: str,
    ) -> bytes:
        """
        Download file bytes.
        """
        raise NotImplementedError

    @abstractmethod
    async def delete(
        self,
        storage_key: str,
    ) -> None:
        """
        Delete stored file.
        """
        raise NotImplementedError

    @abstractmethod
    async def exists(
        self,
        storage_key: str,
    ) -> bool:
        """
        Check whether file exists.
        """
        raise NotImplementedError