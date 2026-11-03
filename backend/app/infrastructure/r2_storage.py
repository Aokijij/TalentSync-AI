"""Private R2 objects, accessed only by the backend with bucket-scoped S3 keys."""
from dataclasses import dataclass
from functools import lru_cache

from botocore.exceptions import BotoCoreError, ClientError

from app.core.config import settings

MAX_OBJECT_BYTES = 5 * 1024 * 1024


@dataclass(frozen=True)
class StoredObject:
    name: str
    size: int
    etag: str


def _key(value: str, *, prefix=False):
    parts = value.removesuffix("/").split("/") if prefix else value.split("/")
    if not value or len(value.encode("utf-8")) > 1024 or "\\" in value or any(ord(char) < 32 for char in value) or any(part in {"", ".", ".."} for part in parts):
        raise ValueError("Identificador de archivo privado inválido")
    return value


def _storage_failure(exc):
    code = exc.response.get("Error", {}).get("Code") if isinstance(exc, ClientError) else None
    if code in {"NoSuchKey", "NotFound", "404"}:
        return FileNotFoundError("Archivo privado no encontrado")
    return OSError("Almacenamiento privado no disponible")


class R2Storage:
    def __init__(self, client, bucket):
        self.client = client
        self.bucket = bucket

    def put(self, key, content, media_type, *, overwrite=False):
        key = _key(key)
        if not content or len(content) > MAX_OBJECT_BYTES:
            raise OSError("Tamaño de archivo privado no válido")
        params = {"Bucket": self.bucket, "Key": key, "Body": content, "ContentType": media_type,
                  "CacheControl": "private, no-store", "StorageClass": "STANDARD"}
        if not overwrite:
            params["IfNoneMatch"] = "*"
        try:
            self.client.put_object(**params)
        except (BotoCoreError, ClientError) as exc:
            raise _storage_failure(exc) from None

    def read(self, key, *, max_bytes=MAX_OBJECT_BYTES, etag=None):
        params = {"Bucket": self.bucket, "Key": _key(key)}
        if etag:
            params["IfMatch"] = etag
        try:
            response = self.client.get_object(**params)
            body = response["Body"]
            try:
                size = response["ContentLength"]
                if not 0 <= size <= max_bytes:
                    raise OSError("Límite de archivo privado superado")
                content = body.read(max_bytes + 1)
                if len(content) != size or len(content) > max_bytes:
                    raise OSError("Archivo privado incompleto o modificado")
                return content
            finally:
                body.close()
        except (BotoCoreError, ClientError) as exc:
            raise _storage_failure(exc) from None

    def list_prefix(self, prefix, *, limit=1000):
        prefix = _key(prefix, prefix=True)
        result, continuation = [], None
        try:
            while True:
                params = {"Bucket": self.bucket, "Prefix": prefix, "MaxKeys": min(1000, max(1, limit + 1 - len(result)))}
                if continuation:
                    params["ContinuationToken"] = continuation
                page = self.client.list_objects_v2(**params)
                for item in page.get("Contents", []):
                    name = item["Key"]
                    if not name.startswith(prefix):
                        raise OSError("Respuesta fuera del ámbito de la cuenta")
                    result.append(StoredObject(_key(name), item["Size"], item["ETag"]))
                    if len(result) > limit:
                        raise OSError("Límite de archivos privados superado")
                if not page.get("IsTruncated"):
                    return result
                next_token = page.get("NextContinuationToken")
                if not next_token or next_token == continuation:
                    raise OSError("Listado privado incompleto")
                continuation = next_token
        except (BotoCoreError, ClientError) as exc:
            raise _storage_failure(exc) from None

    def delete(self, key):
        try:
            self.client.delete_object(Bucket=self.bucket, Key=_key(key))
        except (BotoCoreError, ClientError) as exc:
            raise _storage_failure(exc) from None

    def available(self):
        try:
            self.client.list_objects_v2(Bucket=self.bucket, Prefix="users/", MaxKeys=1)
            return True
        except (BotoCoreError, ClientError):
            return False


@lru_cache(maxsize=4)
def _storage(endpoint, bucket, region, access_key, secret_key):
    import boto3
    from botocore.config import Config

    client = boto3.client("s3", endpoint_url=endpoint, region_name=region,
                          aws_access_key_id=access_key, aws_secret_access_key=secret_key,
                          config=Config(signature_version="s3v4", connect_timeout=3, read_timeout=10,
                                        retries={"mode": "standard", "total_max_attempts": 2},
                                        s3={"addressing_style": "path"},
                                        request_checksum_calculation="when_required",
                                        response_checksum_validation="when_required"))
    return R2Storage(client, bucket)


def get_r2_storage(config=settings):
    if not getattr(config, "r2_endpoint_url", ""):
        return None
    return _storage(config.r2_endpoint_url, config.r2_bucket, config.r2_region,
                    config.r2_access_key_id.get_secret_value(), config.r2_secret_access_key.get_secret_value())
