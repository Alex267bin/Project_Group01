import base64
import io
import json
from typing import TypedDict

import qrcode


class QRPayload(TypedDict):
    session_id: str
    session_code: str


class DynamicQRPayload(QRPayload):
    token: str
    timestamp_bucket: int


def build_qr_payload(session_id: str, session_code: str) -> QRPayload:
    return {"session_id": session_id, "session_code": session_code}


def build_dynamic_qr_payload(
    session_id: str,
    session_code: str,
    token: str,
    timestamp_bucket: int,
) -> DynamicQRPayload:
    return {
        "session_id": session_id,
        "session_code": session_code,
        "token": token,
        "timestamp_bucket": timestamp_bucket,
    }


def generate_qr_data_uri(payload: QRPayload | DynamicQRPayload) -> str:
    payload_bytes = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    image = qrcode.make(payload_bytes)
    output = io.BytesIO()
    image.save(output, format="PNG")
    encoded_image = base64.b64encode(output.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded_image}"


def generate_dynamic_qr_data_uri(payload: DynamicQRPayload) -> str:
    return generate_qr_data_uri(payload)