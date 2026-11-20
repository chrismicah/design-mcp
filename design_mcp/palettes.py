"""Accessible palette generation shared by the server and data pipeline."""

import colorsys

from .models.visual_analyzer import contrast_ratio, hex_to_rgb, rgb_to_hsl

def hsl_to_hex(h, s, l):
    """Convert HSL to hex. h: 0-360, s: 0-100, l: 0-100."""
    r, g, b = colorsys.hls_to_rgb(h / 360, l / 100, s / 100)
    return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"


def generate_shade_scale(hex_color):
    """Generate 11-shade scale (50-950) using perceptual HSL adjustments."""
    r, g, b = hex_to_rgb(hex_color)
    h, s, l = rgb_to_hsl(r, g, b)

    # Shade definitions: (name, lightness_offset, saturation_offset)
    shades = [
        ("50",  +45, -30), ("100", +38, -25), ("200", +28, -15),
        ("300", +18, -5),  ("400", +8,  0),   ("500", 0,   0),
        ("600", -8,  +5),  ("700", -18, +5),  ("800", -28, 0),
        ("900", -38, -10), ("950", -45, -20),
    ]

    scale = {}
    for name, l_off, s_off in shades:
        new_l = max(3, min(97, l + l_off))
        new_s = max(5, min(100, s + s_off))
        scale[name] = hsl_to_hex(h, new_s, new_l)

    return scale


def check_wcag_aa(bg_hex, text_hex):
    """Check if color pair meets WCAG AA (4.5:1 for normal text)."""
    ratio = contrast_ratio(bg_hex, text_hex)
    return ratio >= 4.5, ratio


def generate_accessible_palette(primary_hex, color_mode="dark"):
    """Generate a full semantic token set from a primary color, ensuring WCAG AA."""
    scale = generate_shade_scale(primary_hex)
    r, g, b = hex_to_rgb(primary_hex)
    h, s, l = rgb_to_hsl(r, g, b)

    # Complementary accent
    accent_h = (h + 180) % 360
    accent_hex = hsl_to_hex(accent_h, min(s * 0.8, 80), 50)
    accent_scale = generate_shade_scale(accent_hex)

    # Semantic colors (universal)
    semantic = {
        "success": "#22c55e", "warning": "#f59e0b",
        "error": "#ef4444", "info": "#3b82f6",
    }

    if color_mode == "dark":
        bg = scale["950"]
        bg_secondary = scale["900"]
        bg_card = scale["900"]
        fg = scale["50"]
        fg_secondary = scale["400"]
        fg_muted = scale["500"]
        border = scale["800"]
        ring = scale["300"]
    else:
        bg = "#ffffff"
        bg_secondary = scale["50"]
        bg_card = "#ffffff"
        fg = scale["950"]
        fg_secondary = scale["600"]
        fg_muted = scale["500"]
        border = scale["200"]
        ring = scale["400"]

    # Verify contrast and fix if needed
    passes, ratio = check_wcag_aa(bg, fg)
    if not passes:
        if color_mode == "dark":
            fg = "#f8fafc"
        else:
            fg = "#020617"

    # Ensure primary is visible on background (ratio >= 2.5:1)
    primary_visible = primary_hex
    primary_ratio = contrast_ratio(bg, primary_hex)
    if primary_ratio < 2.5:
        # Push primary to a lighter shade in dark mode, darker in light mode
        if color_mode == "dark":
            primary_visible = scale["400"] if contrast_ratio(bg, scale["400"]) >= 2.5 else scale["300"]
        else:
            primary_visible = scale["600"] if contrast_ratio(bg, scale["600"]) >= 2.5 else scale["700"]

    tokens = {
        "color-background": bg,
        "color-background-secondary": bg_secondary,
        "color-background-card": bg_card,
        "color-foreground": fg,
        "color-foreground-secondary": fg_secondary,
        "color-foreground-muted": fg_muted,
        "color-primary": primary_visible,
        "color-primary-foreground": "#ffffff" if l < 60 else "#000000",
        "color-accent": accent_hex,
        "color-border": border,
        "color-ring": ring,
        "color-success": semantic["success"],
        "color-warning": semantic["warning"],
        "color-error": semantic["error"],
        "color-info": semantic["info"],
        "spacing-xs": "0.25rem",
        "spacing-sm": "0.5rem",
        "spacing-md": "1rem",
        "spacing-lg": "1.5rem",
        "spacing-xl": "2rem",
        "spacing-2xl": "3rem",
        "spacing-section": "4rem",
        "radius-sm": "0.25rem",
        "radius-md": "0.5rem",
        "radius-lg": "0.75rem",
        "radius-xl": "1rem",
        "font-size-xs": "0.75rem",
        "font-size-sm": "0.875rem",
        "font-size-base": "1rem",
        "font-size-lg": "1.125rem",
        "font-size-xl": "1.25rem",
        "font-size-2xl": "1.5rem",
        "font-size-3xl": "1.875rem",
        "font-size-display": "clamp(2.25rem, 5vw, 3.75rem)",
    }

    return tokens, scale, accent_scale
