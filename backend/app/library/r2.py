"""Private R2 read links and object listing."""

import hashlib
import hmac
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen


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


def signed_headers(config: R2Config, method: str, key: str, now: datetime, payload_hash: str = "UNSIGNED-PAYLOAD") -> tuple[str, dict[str, str]]:
    """Authorization headers for one R2 request. No network call is made."""
    host = f"{config.account_id}.r2.cloudflarestorage.com"
    amz_date = now.strftime("%Y%m%dT%H%M%SZ")
    datestamp = now.strftime("%Y%m%d")
    region = "auto"
    credential = f"{config.access_key_id}/{datestamp}/{region}/s3/aws4_request"
    canonical_uri = "/" + quote(config.bucket, safe="") + "/" + quote(key, safe="/")
    names = {
        "host": host,
        "x-amz-content-sha256": payload_hash,
        "x-amz-date": amz_date,
    }
    signed = ";".join(sorted(names))
    canonical_headers = "".join(f"{name}:{names[name]}\n" for name in sorted(names))
    canonical_request = "\n".join([method, canonical_uri, "", canonical_headers, signed, payload_hash])
    scope = f"{datestamp}/{region}/s3/aws4_request"
    string_to_sign = "\n".join(
        ["AWS4-HMAC-SHA256", amz_date, scope, hashlib.sha256(canonical_request.encode()).hexdigest()]
    )
    signature = hmac.new(_signing_key(config.secret_access_key, datestamp, region), string_to_sign.encode(), hashlib.sha256).hexdigest()
    authorization = f"AWS4-HMAC-SHA256 Credential={credential}, SignedHeaders={signed}, Signature={signature}"
    return f"https://{host}{canonical_uri}", {
        "Host": host,
        "X-Amz-Content-Sha256": payload_hash,
        "X-Amz-Date": amz_date,
        "Authorization": authorization,
    }


def list_object_keys(config: R2Config, prefix: str, now: datetime) -> list[str]:
    """List object keys under prefix (S3 ListObjectsV2)."""
    host = f"{config.account_id}.r2.cloudflarestorage.com"
    keys: list[str] = []
    token: str | None = None
    while True:
        params: dict[str, str] = {"list-type": "2", "prefix": prefix}
        if token:
            params["continuation-token"] = token
        query = urlencode(sorted(params.items()))
        canonical_uri = "/" + quote(config.bucket, safe="")
        amz_date = now.strftime("%Y%m%dT%H%M%SZ")
        datestamp = now.strftime("%Y%m%d")
        region = "auto"
        credential = f"{config.access_key_id}/{datestamp}/{region}/s3/aws4_request"
        names = {
            "host": host,
            "x-amz-content-sha256": hashlib.sha256(b"").hexdigest(),
            "x-amz-date": amz_date,
        }
        signed = ";".join(sorted(names))
        canonical_headers = "".join(f"{name}:{names[name]}\n" for name in sorted(names))
        canonical_request = "\n".join(["GET", canonical_uri, query, canonical_headers, signed, names["x-amz-content-sha256"]])
        scope = f"{datestamp}/{region}/s3/aws4_request"
        string_to_sign = "\n".join(
            ["AWS4-HMAC-SHA256", amz_date, scope, hashlib.sha256(canonical_request.encode()).hexdigest()]
        )
        signature = hmac.new(_signing_key(config.secret_access_key, datestamp, region), string_to_sign.encode(), hashlib.sha256).hexdigest()
        authorization = f"AWS4-HMAC-SHA256 Credential={credential}, SignedHeaders={signed}, Signature={signature}"
        url = f"https://{host}{canonical_uri}?{query}"
        request = Request(
            url,
            headers={
                "Host": host,
                "X-Amz-Content-Sha256": names["x-amz-content-sha256"],
                "X-Amz-Date": amz_date,
                "Authorization": authorization,
            },
            method="GET",
        )
        try:
            with urlopen(request, timeout=60) as response:
                payload = response.read()
        except HTTPError as exc:
            raise OSError(f"R2 list failed ({exc.code})") from exc
        except URLError as exc:
            raise OSError(f"R2 list unreachable: {exc}") from exc
        root = ET.fromstring(payload)
        ns = {"s3": "http://s3.amazonaws.com/doc/2006-03-01/"}
        for elem in root.findall(".//s3:Contents/s3:Key", ns):
            if elem.text:
                keys.append(elem.text)
        truncated = root.findtext(".//s3:IsTruncated", default="false", namespaces=ns)
        token_elem = root.find(".//s3:NextContinuationToken", ns)
        if truncated == "true" and token_elem is not None and token_elem.text:
            token = token_elem.text
            continue
        break
    return keys


def _signing_key(secret: str, datestamp: str, region: str) -> bytes:
    def sign(key: bytes, message: str) -> bytes:
        return hmac.new(key, message.encode(), hashlib.sha256).digest()

    dated = sign(f"AWS4{secret}".encode(), datestamp)
    regional = sign(dated, region)
    service = sign(regional, "s3")
    return sign(service, "aws4_request")
