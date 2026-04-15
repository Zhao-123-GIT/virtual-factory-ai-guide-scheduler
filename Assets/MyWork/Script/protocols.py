import struct
import json
from dataclasses import dataclass

# Minimal protocol helpers to unblock server startup.
# They parse the binary framing used by Bytedance OpenSpeech v1 TTS examples.

@dataclass
class Message:
    type: str
    payload: bytes
    sequence: int

class MsgType:
    FrontEndResultServer = "FrontEndResultServer"
    AudioOnlyServer = "AudioOnlyServer"

async def full_client_request(ws, payload: bytes):
    """
    Send a Full Client Request frame: header + payload_size + payload_bytes
    Header format mirrors the example usage:
    - 0x11, 0x10, 0x10, 0x00
    """
    header = struct.pack(">BBBB", 0x11, 0x10, 0x10, 0x00)
    payload_size = struct.pack(">I", len(payload))
    await ws.send(header + payload_size + payload)

async def receive_message(ws) -> Message:
    """
    Receive one framed message and classify:
    Layout we assume (consistent with AudioOnly frames used in examples):
    - 0:4   header (0x11, ...)
    - 4:8   sequence (big-endian signed int), <0 means last chunk
    - 8:12  payload_size (big-endian unsigned int)
    - 12:   payload bytes

    We classify payload as FrontEndResultServer if it looks like UTF-8 JSON;
    otherwise treat it as AudioOnlyServer (binary audio chunk).
    """
    raw = await ws.recv()
    if not isinstance(raw, (bytes, bytearray)):
        return Message(MsgType.FrontEndResultServer, b"", 0)
    data = bytes(raw)
    if len(data) < 12:
        return Message(MsgType.FrontEndResultServer, b"", 0)

    # Parse sequence and payload size
    sequence = struct.unpack(">i", data[4:8])[0]
    payload_size = struct.unpack(">I", data[8:12])[0]
    payload = data[12:12 + payload_size] if len(data) >= 12 + payload_size else b""

    # Try to detect JSON front-end messages
    if payload:
        first = payload[:1]
        if first in (b"{", b"["):
            try:
                json.loads(payload.decode("utf-8"))
                return Message(MsgType.FrontEndResultServer, payload, sequence)
            except Exception:
                pass
    return Message(MsgType.AudioOnlyServer, payload, sequence)
