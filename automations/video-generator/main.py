"""
Genera un video de demo personalizado para un negocio: simula la
conversación de WhatsApp/Telegram (cliente escribe, aparece el menú,
toca "Agendar cita") y sigue con la web de reservas real, todo grabado
en formato vertical (9:16), con narración en español (Gemini TTS).

Uso:
    python main.py --business "Peluquería Estilo" --address "Cra 10 #20-30, Bogotá"

Requiere:
    - BOOKING_API_URL en .env (o --url para apuntar a otro lado, ej. local).
    - GEMINI_API_KEY en .env para la narración (si falta, el video sale sin voz).

Nota: la reserva que hace este script durante la grabación es una reserva de
prueba real (queda en la base de datos del negocio con nombre "Cliente Demo").
Es intencional -- ver el código de confirmación real en pantalla es parte de
lo que hace creíble el video. Si el prospecto se convierte en cliente real,
limpiar esa fila antes de la entrega.
"""
import argparse
import os
import subprocess
import sys
import wave
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

import imageio_ffmpeg
import requests
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

sys.path.append(str(Path(__file__).parent))
from narration import synthesize  # noqa: E402

load_dotenv()

OUTPUT_DIR = Path(__file__).parent / "output"
CHAT_TEMPLATE = Path(__file__).parent / "chat_template.html"
VIEWPORT = {"width": 390, "height": 844}  # proporción vertical tipo celular (9:16 aprox)
COLD_START_TIMEOUT = 60_000  # Render free tier puede tardar ~50s en despertar


def wake_up(base_url: str, timeout: int = 90):
    """Le pega a /health hasta que responda 200, para que Render termine de
    'despertar' el servicio ANTES de empezar a grabar -- si no, la pantalla
    de 'spinning up' de Render queda grabada en vez de la web real."""
    import time

    url = base_url.rstrip("/") + "/health"
    deadline = time.time() + timeout
    print("  despertando el servidor (puede tardar ~30-50s si estaba dormido)...")
    while time.time() < deadline:
        try:
            r = requests.get(url, timeout=10)
            if r.ok:
                return
        except requests.exceptions.RequestException:
            pass
        time.sleep(2)
    print("  [aviso] el servidor no respondió a tiempo, seguimos igual (puede que la grabación arranque lenta).")


def get_wav_duration(path: Path) -> float:
    with wave.open(str(path), "rb") as f:
        return f.getnframes() / f.getframerate()


def set_caption(page, text: str):
    page.evaluate(
        """(text) => {
            let bar = document.getElementById('demo-caption');
            if (!bar) {
                bar = document.createElement('div');
                bar.id = 'demo-caption';
                bar.style.cssText = 'position:fixed;bottom:24px;left:16px;right:16px;'
                    + 'background:rgba(0,0,0,0.78);color:#fff;padding:14px 16px;'
                    + 'border-radius:12px;font-family:-apple-system,sans-serif;'
                    + 'font-size:17px;font-weight:600;text-align:center;z-index:999999;'
                    + 'box-shadow:0 4px 16px rgba(0,0,0,0.3);';
                document.body.appendChild(bar);
            }
            bar.textContent = text;
        }""",
        text,
    )


def record_chat_intro(business: str, video_dir: Path, min_duration: float) -> Path:
    """Simula la conversación de chat (mensaje del cliente, menú, toque en
    'Agendar cita') y la graba. `min_duration` asegura que el clip dure al
    menos lo que tarda la narración, para no cortarla."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(
            viewport=VIEWPORT,
            record_video_dir=str(video_dir),
            record_video_size=VIEWPORT,
        )
        page = context.new_page()

        elapsed = 0

        def wait(ms):
            nonlocal elapsed
            page.wait_for_timeout(ms)
            elapsed += ms

        page.goto(f"file://{CHAT_TEMPLATE}?business={quote(business)}", wait_until="load")
        wait(700)

        page.evaluate("addMessage('Hola', 'out')")
        wait(900)
        page.evaluate("showTyping()")
        wait(1300)
        page.evaluate("hideTyping()")
        page.evaluate(
            "(name) => addMessage('¡Hola! 👋 Bienvenido a ' + name + '. ¿En qué te ayudamos hoy?', 'in')",
            business,
        )
        wait(1600)
        page.evaluate("showMenu()")
        wait(1800)
        page.evaluate("pressCita()")
        wait(1000)

        remaining = min_duration * 1000 - elapsed
        if remaining > 0:
            wait(int(remaining) + 500)

        context.close()
        video_path = Path(page.video.path())
        browser.close()

    return video_path


def record_booking_flow(business: str, phone: str, address: str, base_url: str, video_dir: Path, min_duration: float) -> Path:
    booking_url = (
        f"{base_url.rstrip('/')}/?business={quote(business)}"
        f"&phone={quote(phone)}&address={quote(address)}"
    )

    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(
            viewport=VIEWPORT,
            record_video_dir=str(video_dir),
            record_video_size=VIEWPORT,
        )
        page = context.new_page()
        page.set_default_timeout(COLD_START_TIMEOUT)

        elapsed = 0

        def wait(ms):
            nonlocal elapsed
            page.wait_for_timeout(ms)
            elapsed += ms

        page.goto(booking_url, wait_until="load")
        set_caption(page, f"Así se ve la reserva para {business}")
        wait(2000)

        page.click(".service-card")
        set_caption(page, "El cliente elige el servicio...")
        wait(1400)

        page.click("#btn-to-2")
        set_caption(page, "...y el día y la hora que más le convengan")
        page.wait_for_selector(".day-chip", timeout=COLD_START_TIMEOUT)
        page.click(".day-chip >> nth=0")

        page.wait_for_selector(".time-chip:not([disabled])", timeout=COLD_START_TIMEOUT)
        page.click(".time-chip:not([disabled]) >> nth=0")
        wait(1200)

        page.click("#btn-to-3")
        set_caption(page, "Completa sus datos...")
        page.fill("#input-name", "Cliente Demo")
        page.fill("#input-phone", "300 000 0000")
        wait(1400)

        set_caption(page, "...y listo")
        page.click("#btn-confirm")
        page.wait_for_selector("#step-4:not([hidden])", timeout=COLD_START_TIMEOUT)
        set_caption(page, "¡Cita confirmada automáticamente! 🙌")
        wait(2500)

        remaining = min_duration * 1000 - elapsed
        if remaining > 0:
            wait(int(remaining) + 500)

        context.close()
        video_path = Path(page.video.path())
        browser.close()

    return video_path


def chat_narration_text(business: str) -> str:
    return (
        f"Un cliente le escribe a {business} preguntando por una cita. "
        "En segundos, el bot responde con un menú: agendar cita, ver servicios, "
        "el horario, o la ubicación. El cliente toca 'agendar cita', y listo."
    )


def booking_narration_text(business: str) -> str:
    return (
        "Ahí elige el servicio que necesita, el día y la hora que más le convengan, "
        "completa su nombre y su teléfono, y confirma. En segundos queda la cita "
        "registrada, con un código de confirmación real -- sin que nadie del "
        "negocio haya tenido que contestar un solo mensaje."
    )


def mux(video_path: Path, audio_path, out_path: Path):
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    if audio_path:
        cmd = [
            ffmpeg, "-y",
            "-i", str(video_path),
            "-i", str(audio_path),
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-shortest",
            str(out_path),
        ]
    else:
        cmd = [ffmpeg, "-y", "-i", str(video_path), "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out_path)]
    subprocess.run(cmd, check=True, capture_output=True)


def concat(parts: list, out_path: Path):
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    list_file = out_path.parent / "concat_list.txt"
    list_file.write_text("\n".join(f"file '{p.resolve()}'" for p in parts))
    cmd = [
        ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", str(list_file),
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", str(out_path),
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    list_file.unlink()


def try_synthesize(text: str, out_path: Path):
    try:
        synthesize(text, out_path)
        return out_path, get_wav_duration(out_path)
    except Exception as exc:
        print(f"  [aviso] no se pudo generar narración ({exc}), ese tramo queda sin audio.")
        return None, 4.0  # duración mínima de respaldo si no hay narración


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--business", required=True)
    parser.add_argument("--phone", default="+57 300 000 0000")
    parser.add_argument("--address", default="Cra 15 #93-47, Bogotá")
    parser.add_argument("--url", default=os.getenv("BOOKING_API_URL"), help="Base URL de booking-api")
    args = parser.parse_args()

    if not args.url:
        print("Falta la URL de booking-api. Pasala con --url o poné BOOKING_API_URL en .env.")
        return

    OUTPUT_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    work_dir = OUTPUT_DIR / f"raw_{stamp}"
    work_dir.mkdir()

    print("Generando narración...")
    chat_audio, chat_min_dur = try_synthesize(chat_narration_text(args.business), work_dir / "narracion_chat.wav")
    booking_audio, booking_min_dur = try_synthesize(booking_narration_text(args.business), work_dir / "narracion_booking.wav")

    wake_up(args.url)  # antes de grabar nada, para que Render no muestre su pantalla de "despertando"

    print(f"Grabando simulación de chat para '{args.business}'...")
    chat_video = record_chat_intro(args.business, work_dir / "chat", chat_min_dur)

    print("Grabando flujo de reserva...")
    booking_video = record_booking_flow(args.business, args.phone, args.address, args.url, work_dir / "booking", booking_min_dur)

    print("Armando el video...")
    chat_mp4 = work_dir / "chat.mp4"
    booking_mp4 = work_dir / "booking.mp4"
    mux(chat_video, chat_audio, chat_mp4)
    mux(booking_video, booking_audio, booking_mp4)

    safe_name = "".join(c if c.isalnum() else "_" for c in args.business).strip("_")
    final_path = OUTPUT_DIR / f"demo_{safe_name}_{stamp}.mp4"
    concat([chat_mp4, booking_mp4], final_path)

    print(f"\nListo: {final_path}")


if __name__ == "__main__":
    main()
