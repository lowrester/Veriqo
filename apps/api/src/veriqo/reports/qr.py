"""QR code generation for reports."""

import io
from pathlib import Path
from typing import Optional

import qrcode
from PIL import Image
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.colormasks import SolidFillColorMask
from qrcode.image.styles.moduledrawers import RoundedModuleDrawer


def generate_qr_code(
    url: str,
    size: int = 200,
    primary_color: str = "#2563eb",
    logo_path: Optional[Path] = None,
) -> io.BytesIO:
    """
    Generate a branded QR code for report access.

    Args:
        url: The URL to encode
        size: Output image size in pixels
        primary_color: Brand color for QR modules
        logo_path: Optional logo to embed in center

    Returns:
        BytesIO buffer containing PNG image
    """
    # Convert hex to RGB tuple
    color = tuple(int(primary_color.lstrip("#")[i : i + 2], 16) for i in (0, 2, 4))

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_H
        if logo_path
        else qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=2,
    )

    qr.add_data(url)
    qr.make(fit=True)

    # Create styled image
    img = qr.make_image(
        image_factory=StyledPilImage,
        module_drawer=RoundedModuleDrawer(),
        color_mask=SolidFillColorMask(
            back_color=(255, 255, 255),
            front_color=color,
        ),
    )

    # Convert to PIL Image for resizing
    if hasattr(img, "get_image"):
        pil_img = img.get_image()
    else:
        pil_img = img

    # Resize to target size
    pil_img = pil_img.resize((size, size), Image.Resampling.LANCZOS)

    # Embed logo if provided
    if logo_path and logo_path.exists():
        pil_img = _embed_logo(pil_img, logo_path)

    # Export to buffer
    buffer = io.BytesIO()
    pil_img.save(buffer, format="PNG")
    buffer.seek(0)

    return buffer


def _embed_logo(qr_img: Image.Image, logo_path: Path) -> Image.Image:
    """Embed a logo in the center of the QR code."""
    logo = Image.open(logo_path)

    # Logo should be ~20% of QR code size
    qr_size = qr_img.size[0]
    logo_size = int(qr_size * 0.2)
    logo = logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)

    # Create white background for logo
    bg_size = int(logo_size * 1.1)
    bg = Image.new("RGBA", (bg_size, bg_size), (255, 255, 255, 255))

    # Center logo on background
    offset = (bg_size - logo_size) // 2
    bg.paste(logo, (offset, offset), logo if logo.mode == "RGBA" else None)

    # Paste on QR code
    pos = (qr_size - bg_size) // 2
    qr_img.paste(bg, (pos, pos))

    return qr_img


def generate_access_token() -> str:
    """Generate a cryptographically secure access token."""
    import secrets

    return secrets.token_urlsafe(32)  # 256 bits of entropy
