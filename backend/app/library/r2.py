"""Private R2 read links. This module does not request the object."""

import hashlib
import hmac
from dataclasses import dataclass
from datetime import datetime
from urllib.parse import quote


@dataclass(frozen=True)
class R2Config:
    account_id: str
    bucket: str
    access_key_id: str
    secret_access_key: str


def presign_get(config: R2Config, key: str, now: datetime, expires: int = 300) -> str:
    """Build an https GET URL. No network call is made."""
    host = f"{config.account_id}.r2.cloudflarestorage.com"
    amz_date = now.strftime("%Y%m%dT%H%M%SZ")
    datestamp = now.strftime("%Y%m%d")
    region = "auto"
    credential = f"{config.access_key_id}/{datestamp}/{region}/s3/aws4_request"
    canonical_uri = "/" + quote(config.bucket, safe="") + "/" + quote(key, safe="/")
    params = {
        "X-Amz-Algorithm": "AWS4-HMAC-SHA256",
        "X-Amz-Credential": credential,
        "X-Amz-Date": amz_date,
        "X-Amz-Expires": str(expires),
        "X-Amz-SignedHeaders": "host",
    }
    canonical_query = "&".join(
        f"{quote(name, safe='')}={quote(params[name], safe='')}" for name in sorted(params)
    )
    canonical_request = "\n".join(
        [
            "GET",
            canonical_uri,
            canonical_query,
            f"host:{host}\n",
            "host",
            "UNSIGNED-PAYLOAD",
        ]
    )
    scope = f"{datestamp}/{region}/s3/aws4_request"
    string_to_sign = "\n".join(
        [
            "AWS4-HMAC-SHA256",
            amz_date,
            scope,
            hashlib.sha256(canonical_request.encode()).hexdigest(),
        ]
    )
    signing_key = _signing_key(config.secret_access_key, datestamp, region)
    signature = hmac.new(signing_key, string_to_sign.encode(), hashlib.sha256).hexdigest()
    return f"https://{host}{canonical_uri}?{canonical_query}&X-Amz-Signature={signature}"


def _signing_key(secret: str, datestamp: str, region: str) -> bytes:
    def sign(key: bytes, message: str) -> bytes:
        return hmac.new(key, message.encode(), hashlib.sha256).digest()

    dated = sign(f"AWS4{secret}".encode(), datestamp)
    regional = sign(dated, region)
    service = sign(regional, "s3")
    return sign(service, "aws4_request")
