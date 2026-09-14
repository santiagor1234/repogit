"""
Genera un video de demo personalizado para un negocio: controla un
navegador real contra la web de reservas (booking-api), lo graba en
formato vertical (9:16, para Reels/TikTok), le agrega narración por voz
(Gemini TTS) y arma un .mp4 listo para publicar.

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
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

import imageio_ffmpeg
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

sys.path.append(str(Path(__file__).parent))
from narration import synthesize  # noqa: E402

load_dotenv()

OUTPUT_DIR = Path(__file__).parent / "output"
VIEWPORT = {"width": 390, "height": 844}  # proporción vertical tipo celular (9:16 aprox)
COLD_START_TIMEOUT = 60_000  # Render free tier puede tardar ~50s en despertar


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


def record_demo(business: str, phone: str, address: str, base_url: str, video_dir: Path) -> Path:
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

        page.goto(booking_url, wait_until="load")
        set_caption(page, f"Así se ve la reserva para {business}")
        page.wait_for_timeout(1800)

        page.click(".service-card")
        set_caption(page, "El cliente elige el servicio...")
        page.wait_for_timeout(1200)

        page.click("#btn-to-2")
        set_caption(page, "...y el día y la hora que más le convengan")
        page.wait_for_selector(".day-chip", timeout=COLD_START_TIMEOUT)
        page.click(".day-chip >> nth=0")

        page.wait_for_selector(".time-chip:not([disabled])", timeout=COLD_START_TIMEOUT)
        page.click(".time-chip:not([disabled]) >> nth=0")
        page.wait_for_timeout(800)

        page.click("#btn-to-3")
        set_caption(page, "Completa sus datos...")
        page.fill("#input-name", "Cliente Demo")
        page.fill("#input-phone", "300 000 0000")
        page.wait_for_timeout(1000)

        set_caption(page, "...y listo")
        page.click("#btn-confirm")
        page.wait_for_selector("#step-4:not([hidden])", timeout=COLD_START_TIMEOUT)
        set_caption(page, "¡Cita confirmada automáticamente! 🙌")
        page.wait_for_timeout(2500)

        context.close()  # necesario para que el .webm quede escrito en disco
        video_path = Path(page.video.path())
        browser.close()

    return video_path


def build_narration_text(business: str) -> str:
    return (
        f"Así se ve la reserva para {business}. El cliente elige el servicio, "
        "el día y la hora que más le convengan, completa sus datos, y en segundos "
        "queda la cita confirmada, sin que nadie del negocio tenga que contestar "
        "un solo mensaje."
    )


def merge_audio_video(video_path: Path, audio_path: Path, out_path: Path):
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [
        ffmpeg, "-y",
        "-i", str(video_path),
        "-i", str(audio_path),
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-shortest",
        str(out_path),
    ]
    subprocess.run(cmd, check=True, capture_output=True)


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

    print(f"Grabando demo para '{args.business}'...")
    video_path = record_demo(args.business, args.phone, args.address, args.url, work_dir)
    print(f"  video crudo: {video_path}")

    audio_path = work_dir / "narracion.wav"
    try:
        synthesize(build_narration_text(args.business), audio_path)
        print(f"  narración: {audio_path}")
    except Exception as exc:
        print(f"  [aviso] no se pudo generar narración ({exc}), el video queda sin audio.")
        audio_path = None

    safe_name = "".join(c if c.isalnum() else "_" for c in args.business).strip("_")
    final_path = OUTPUT_DIR / f"demo_{safe_name}_{stamp}.mp4"

    if audio_path:
        merge_audio_video(video_path, audio_path, final_path)
    else:
        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
        subprocess.run(
            [ffmpeg, "-y", "-i", str(video_path), "-c:v", "libx264", "-pix_fmt", "yuv420p", str(final_path)],
            check=True, capture_output=True,
        )

    print(f"\nListo: {final_path}")


if __name__ == "__main__":
    main()
