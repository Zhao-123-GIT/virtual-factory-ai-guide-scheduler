import asyncio
import websockets
import json
import struct
import uuid
import aiohttp
import os
import sys
import logging
import array
import time
import re

# ====== 日志 ======
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ====== 将 example/protocols 加入路径，用于 TTS 二进制协议 ======
BASE_DIR = os.path.dirname(__file__)
EXAMPLE_DIR = os.path.join(BASE_DIR, "example")
if EXAMPLE_DIR not in sys.path:
    sys.path.append(EXAMPLE_DIR)
from protocols import MsgType, full_client_request, receive_message  # 复用官方协议工具





# ===================== 配置 =====================
ASR_URL = "wss://openspeech.bytedance.com/api/v3/sauc/bigmodel_async"
APP_KEY = "3581905229"          
ACCESS_KEY = "9ox0kcQlQUMlBwpQn8YMbHgaQYlQzb8K"  
RESOURCE_ID = "volc.bigasr.sauc.duration"

# Android 端口改为 5000
SERVER_BIND_PORT = 5000
# ===================== 配置 =====================

# LLM
LLM_URL = "http://127.0.0.1:11434/api/generate"
LLM_MODEL = "qwen2.5:7b-instruct-q4_K_M"
# LLM


# TTS（二进制 v1）配置
TTS_URL = "wss://openspeech.bytedance.com/api/v1/tts/ws_binary"
VOICE_TYPE = "ICL_zh_male_jijiaozhineng_tob"
CLUSTER = "volcano_tts"
# TTS（二进制 v1）配置


# 唤醒词与静音收尾
WAKE_WORD = "小智"                 # 唤醒词，未唤醒时仅监听该词
AWAKE_SILENCE_LIMIT_SEC = 2.0     # 唤醒后静音2秒结束本段
WAKE_ENABLED = True              # 唤醒模式开关；True 时启用唤醒门控

WAKE_ALIASES = [
    "小智", "小致", "小制", "小志", "晓智", "小支",
    "嘿小智", "你好小智", "助手", "嘿助手", "你好助手"
]

def _normalize_text_for_wake(s: str) -> str:
    return s.replace(" ", "").replace("，", "").replace(",", "").replace("。", "").replace(".", "")

def match_wake_alias(text: str) -> str | None:
    t = _normalize_text_for_wake(text)
    for w in WAKE_ALIASES:
        if w in t:
            return w
    return None

def remove_wake_aliases(text: str) -> str:
    """移除文本中出现的唤醒别名（允许字符间隔符号/空格）。"""
    sep = r"[\s，,。．.、:：;；\-—_~]*"
    t = text
    for w in WAKE_ALIASES:
        pattern = sep.join(map(re.escape, list(w)))
        t = re.sub(pattern, "", t)
    return t.strip()

def cut_tail_after_aliases(text: str) -> str:
    """在出现任一唤醒别名后，仅保留其后的内容（清空之前文本）。支持别名字符间存在分隔符。"""
    sep = r"[\s，,。．.、:：;；\-—_~]*"
    earliest_start = None
    earliest_end = None
    for w in WAKE_ALIASES:
        pattern = sep.join(map(re.escape, list(w)))
        m = re.search(pattern, text)
        if m:
            if earliest_start is None or m.start() < earliest_start:
                earliest_start = m.start()
                earliest_end = m.end()
    if earliest_end is not None:
        return text[earliest_end:].strip()
    return text

# 音频参数
SAMPLE_RATE = 16000
CHANNELS = 1
SEQ_COUNTER = 1

# 静音检测参数：连续静音达到阈值触发分段
SILENCE_THRESHOLD = 500   # PCM16峰值阈值（降低，减少误判静音）
SILENCE_LIMIT_SEC = 1.2   # 静音触发分段时长（稍短，更快切段）
NO_TEXT_LIMIT_SEC = 5.0   # ASR增量文本超时（延长，避免过早结束）



# ===================== 工具函数：ASR 协议 =====================
def build_full_client_request(payload_json):
    payload_bytes = json.dumps(payload_json).encode("utf-8")
    header = struct.pack(">BBBB", 0x11, 0x10, 0x10, 0)
    payload_size = struct.pack(">I", len(payload_bytes))
    return header + payload_size + payload_bytes


def build_audio_only_request_with_seq(audio_bytes, seq):
    header = struct.pack(">BBBB", 0x11, 0x21, 0x00, 0)
    seq_bytes = struct.pack(">I", seq)
    payload_size = struct.pack(">I", len(audio_bytes))
    return header + seq_bytes + payload_size + audio_bytes


def parse_full_server_response(data):
    """解析字节流中的ASR响应"""
    if len(data) < 12:
        return None
    message_type = (data[1] >> 4) & 0xF
    if message_type != 0x9:
        return None
    payload_size = struct.unpack(">I", data[8:12])[0]
    if len(data) < 12 + payload_size:
        return None
    payload = data[12:12 + payload_size]
    try:
        return json.loads(payload.decode("utf-8"))
    except Exception:
        return None

# ===================== LLM =====================
def load_system_prompt():
    try:
        path = os.path.join(BASE_DIR, "ReadMe.md")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()
                return (text[:2000]).strip() or "你是本项目的语音助理。输出简洁、适合播报，使用简体中文；避免长段推理或代码；无关问题礼貌简短回复。"
    except Exception:
        pass
    return "你是本项目的语音助理。输出简洁、适合播报，使用简体中文；避免长段推理或代码；无关问题礼貌简短回复。"

async def query_llm(prompt):
    payload = {
        "model": LLM_MODEL,
        "prompt": prompt,
        "stream": False,
        "system": load_system_prompt(),
        "options": {
            "temperature": 0.3,
            "num_predict": 256,
            "num_ctx": 8192,
            "top_p": 0.9
        }
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(LLM_URL, json=payload) as resp:
                result = await resp.json()
                return result.get("response", "（无返回）")
    except Exception as e:
        logger.warning(f"LLM 调用出错: {e}")
        return "（无法连接LLM）"

# ===================== TTS（v1 二进制） =====================
async def synthesize_tts(text: str) -> bytes:
    """调用 TTS，返回 PCM16 16k 原始字节"""
    headers = {"Authorization": f"Bearer;{ACCESS_KEY}"}
    audio_bytes = bytearray()

    async with websockets.connect(
        TTS_URL,
        additional_headers=headers,
        max_size=10 * 1024 * 1024,
    ) as tts_ws:
        try:
            logid = tts_ws.response.headers.get("x-tt-logid")
            if logid:
                logger.info(f"TTS Connected, Logid: {logid}")
        except Exception:
            pass

        # TTS 请求体
        request = {
            "app": {
                "appid": APP_KEY,
                "token": ACCESS_KEY,
                "cluster": CLUSTER,
            },
            "user": {"uid": str(uuid.uuid4())},
            "audio": {
                "voice_type": VOICE_TYPE,
                "encoding": "pcm",
                "rate": SAMPLE_RATE,
            },
            "request": {
                "reqid": str(uuid.uuid4()),
                "text": text,
                "operation": "submit",
                "with_timestamp": "0",
            },
        }

        # 发送 Full Client Request
        await full_client_request(tts_ws, json.dumps(request).encode())

        # 接收音频（二进制 ACK）
        while True:
            msg = await receive_message(tts_ws)
            if msg.type == MsgType.FrontEndResultServer:
                continue
            elif msg.type == MsgType.AudioOnlyServer:
                audio_bytes.extend(msg.payload)
                if msg.sequence < 0:
                    break
            else:
                raise RuntimeError(f"TTS 合成失败: {msg}")

    return bytes(audio_bytes)

# ===================== ASR 流式处理（含回传 TTS） =====================
async def handle_audio_stream(reader, writer):
    global SEQ_COUNTER
    client_addr = writer.get_extra_info("peername")
    logger.info(f"🎧 收到来自 Android 的连接: {client_addr}")

    headers = [
        ("X-Api-App-Key", APP_KEY),
        ("X-Api-Access-Key", ACCESS_KEY),
        ("X-Api-Resource-Id", RESOURCE_ID),
        ("X-Api-Connect-Id", str(uuid.uuid4())),
    ]

    try:
        # 外层循环：静音分段后重连 ASR
        while True:
            SEQ_COUNTER = 1
            current_text = ""
            silence_event = asyncio.Event()
            speech_started = False  # 新增：检测是否开始说话
            awake = False           # 新增：唤醒状态，只有唤醒后才识别与回复

            async with websockets.connect(
                ASR_URL,
                additional_headers=headers,
                subprotocols=["speech_binary"],
            ) as asr_ws:
                payload = {
                    "user": {"uid": str(uuid.uuid4())},
                    "audio": {
                        "format": "pcm",
                        "rate": SAMPLE_RATE,
                        "bits": 16,
                        "channel": CHANNELS,
                        "language": "zh-CN",
                    },
                    "request": {
                        "model_name": "bigmodel",
                        "enable_itn": True,
                        "enable_punc": True,
                        "enable_ddc": True,
                    },
                }
                await asr_ws.send(build_full_client_request(payload))

                # === 音频发送任务（含静音检测，触发分段） ===
                async def send_to_asr():
                    nonlocal current_text, speech_started, awake
                    global SEQ_COUNTER
                    silent_accum = 0.0
                    while not silence_event.is_set():
                        try:
                            data = await asyncio.wait_for(reader.read(4096), timeout=2.5)
                        except asyncio.TimeoutError:
                            logger.info("⏳ 读Android音频超时，视为上游停发，结束当前段")
                            silence_event.set()
                            break
                        
                        if not data:
                            # Android 断流，结束当前段
                            silence_event.set()
                            break

                        # 静音检测：计算峰值
                        arr = array.array('h')
                        arr.frombytes(data)
                        peak = max(abs(s) for s in arr) if arr else 0
                        frame_dur = len(data) / (2 * SAMPLE_RATE)  # 秒
                        if peak < SILENCE_THRESHOLD:
                            silent_accum += frame_dur
                        else:
                            silent_accum = 0.0
                            if not speech_started:
                                speech_started = True  # 首次检测到非静音，标记开始说话

                        SEQ_COUNTER += 1
                        packet = build_audio_only_request_with_seq(data, SEQ_COUNTER)
                        await asr_ws.send(packet)

                        # 仅在唤醒后使用 2s 静音作为收尾；未唤醒时不因静音结束
                        if WAKE_ENABLED:
                            effective_limit = AWAKE_SILENCE_LIMIT_SEC if awake else float("inf")
                        else:
                            effective_limit = AWAKE_SILENCE_LIMIT_SEC
                        if silent_accum >= effective_limit:
                            logger.info(f"⏱️ 检测到连续静音 {effective_limit}s，结束当前段")
                            silence_event.set()
                            break

                    # 断开 ASR（作为本段结束标记）
                    try:
                        await asr_ws.close()
                        logger.info("🔌 已断开 ASR 连接（静音触发）")
                    except Exception:
                        pass
                    logger.info("📤 音频发送结束")

                # === 接收 ASR 结果任务（增量输出 + 最终 + 无文本超时） ===
                async def recv_from_asr_and_reply():
                    nonlocal current_text, speech_started, awake
                    last_text_time = time.monotonic()
                    last_text_value = ""
                    try:
                        while True:
                            # 使用短超时以便周期性检查无文本超时与静音事件
                            try:
                                raw = await asyncio.wait_for(asr_ws.recv(), timeout=0.3)
                            except asyncio.TimeoutError:
                                if silence_event.is_set():
                                    logger.info("✅ 静音收尾，使用当前文本作为最终结果")
                                    break
                                # 不再使用无文本超时；保持持续识别
                                continue

                            if not isinstance(raw, bytes):
                                continue
                            result = parse_full_server_response(raw)
                            if not result:
                                continue

                            asr_result = result.get("result", {})
                            text = asr_result.get("text", "")
                            is_final = asr_result.get("is_final", False)

                            if text:
                                if WAKE_ENABLED:
                                    if not awake:
                                        alias = match_wake_alias(text)
                                        if alias:
                                            awake = True
                                            speech_started = True
                                            last_text_time = time.monotonic()
                                            logger.info(f"🔔 唤醒触发：{alias}")
                                            # 仅保留别名后的内容，并移除别名字样（每次增量都应用）
                                            text = cut_tail_after_aliases(text)
                                            text = remove_wake_aliases(text)
                                            if text:
                                                current_text = text
                                                last_text_value = text
                                                print(f"🗣️ 实时识别：{text}", end="\r")
                                        else:
                                            continue
                                    else:
                                        # 唤醒后：每次增量都重新在别名之后截断并清理别名
                                        text = cut_tail_after_aliases(text)
                                        text = remove_wake_aliases(text)
                                        if text:
                                            current_text = text
                                            if text != last_text_value:
                                                last_text_value = text
                                                last_text_time = time.monotonic()
                                            print(f"🗣️ 实时识别：{text}", end="\r")
                                else:
                                    # 关闭唤醒：直接累计文本，便于排查ASR与链路问题
                                    current_text = text
                                    if not speech_started:
                                        speech_started = True
                                    if text != last_text_value:
                                        last_text_value = text
                                        last_text_time = time.monotonic()
                                    print(f"🗣️ 实时识别：{text}", end="\r")

                            # 不以 is_final 作为收尾触发，统一由 2s 静音控制
                    except Exception as e:
                        logger.warning(f"ASR 接收任务异常: {e}")

                await asyncio.gather(send_to_asr(), recv_from_asr_and_reply())

            # === 本段结束：使用 current_text 作为最终文本，调用 LLM & TTS ===
            final_text = current_text.strip()
            # 关闭唤醒或已唤醒时触发 LLM/TTS
            if final_text and ((not WAKE_ENABLED) or awake):
                print(f"\n📘 最终文本：{final_text}")
                llm_reply = await query_llm(final_text)
                print(f"🤖 LLM回复：{llm_reply}")
                try:
                    tts_audio = await synthesize_tts(llm_reply)
                    if tts_audio:
                        writer.write(tts_audio)
                        await writer.drain()
                        logger.info(f"🔊 已回传 TTS 音频（{len(tts_audio)} 字节）")
                        # 等待播放完成后再继续录音（按音频时长估算）
                        tts_dur = len(tts_audio) / (2 * SAMPLE_RATE * CHANNELS)
                        await asyncio.sleep(tts_dur + 0.2)
                    else:
                        logger.warning("未获取到 TTS 音频数据")
                except Exception as e:
                    logger.error(f"TTS 合成异常: {e}")
            else:
                logger.info("🔕 未唤醒或无文本，跳过应答")

            # 完成一次回复后复位唤醒状态
            awake = False

            # Android 连接已关闭则退出
            if reader.at_eof():
                break

            # 继续下一段：自动重连 ASR

    except Exception as e:
        logger.error(f"⚠️ ASR处理异常: {e}")

    finally:
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass
        logger.info("🔌 连接关闭")

# ===================== 主程序入口 =====================
async def main():
    server = await asyncio.start_server(handle_audio_stream, "0.0.0.0", SERVER_BIND_PORT)
    print(f"🚀 ASR+LLM+TTS 服务器已启动，监听 TCP 端口 {SERVER_BIND_PORT}")
    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    asyncio.run(main())
