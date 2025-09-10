# utils.py
import io
import qrcode
import base64
from urllib.parse import urlencode
import time
import datetime


def generate_qr_image_data(usergroupcode, domain, timestamp=None):
    """ 
    Function generates QR code and url to the code
    """
    if not timestamp:
        timestamp = int(time.time())
    query_params = urlencode({
        'usergroup': usergroupcode,
        'qr_timestamp': timestamp,
    })
    qr_url = f"{domain}/locator/generatepositonqr/?{query_params}"

    qr = qrcode.make(qr_url)
    buffer = io.BytesIO()
    qr.save(buffer, format="PNG")
    img_base64 = base64.b64encode(buffer.getvalue()).decode()
    qr_image_data = f"data:image/png;base64,{img_base64}"

    return qr_url, qr_image_data


def convert_timestamp_to_fields(timestamp_ms, created_at=None):
    # covert timestamp to seconds from millseconds
    dt = datetime.datetime.fromtimestamp(timestamp_ms / 1000.0)
    # Extract date and time
    date_part = dt.date()
    time_part = dt.time()

    # remove the z from created at
    if created_at:
        try:
            offline_captured = datetime.datetime.fromisoformat(
                created_at.replace("z", "+00.00"))
        except Exception:
            offline_captured = dt
    else:
        offline_captured = dt
    return date_part, time_part, offline_captured
