"""
Nika color system — FA4616 (orange) on F5F5F5 (light gray).

Terminal ANSI escape sequences mapping the Nika brand palette
to 256-color and true-color terminals.
"""

# ── Brand palette ──────────────────────────────────────────────
NIKA_ORANGE = "#FA4616"  # Primary accent — text, highlights, borders
NIKA_GRAY   = "#F5F5F5"  # Background — light gray surface
NIKA_DIM    = "#B0B0B0"  # Muted text
NIKA_WHITE  = "#FFFFFF"  # Pure white for contrast

# ── ANSI true-color escapes (24-bit) ──────────────────────────
# Format: \033[38;2;R;G;Bm  (foreground)
#         \033[48;2;R;G;Bm  (background)
ORANGE_FG = "\033[38;2;250;70;22m"
GRAY_BG   = "\033[48;2;245;245;245m"
DIM_FG    = "\033[38;2;176;176;176m"
WHITE_FG  = "\033[38;2;255;255;255m"
ORANGE_BG = "\033[48;2;250;70;22m"

RESET     = "\033[0m"
BOLD      = "\033[1m"
DIM       = "\033[2m"

# ── Composite styles ──────────────────────────────────────────
HEADER    = f"{BOLD}{ORANGE_FG}"
ACCENT    = f"{ORANGE_FG}"
MUTED     = f"{DIM_FG}"
BANNER_BG = f"{WHITE_FG}{ORANGE_BG}{BOLD}"

# ── Box-drawing characters ────────────────────────────────────
BOX_H  = "─"
BOX_V  = "│"
BOX_TL = "┌"
BOX_TR = "┐"
BOX_BL = "└"
BOX_BR = "┘"
BOX_T  = "┬"
BOX_B  = "┴"
BOX_L  = "├"
BOX_R  = "┤"
DOT    = "●"
ARROW  = "→"
BULLET = "▸"


def nika_box(title: str, body: str, width: int = 60) -> str:
    """Render a Nika-branded box with orange borders."""
    lines = body.split("\n")
    top = f"{ACCENT}{BOX_TL}{BOX_H * (width - 2)}{BOX_TR}{RESET}"
    title_line = f"{ACCENT}{BOX_V}{RESET} {HEADER}{title.center(width - 4)}{RESET} {ACCENT}{BOX_V}{RESET}"
    sep = f"{ACCENT}{BOX_L}{BOX_H * (width - 2)}{BOX_R}{RESET}"
    bottom = f"{ACCENT}{BOX_BL}{BOX_H * (width - 2)}{BOX_BR}{RESET}"

    content_lines = []
    for line in lines:
        padded = line.ljust(width - 4)[:width - 4]
        content_lines.append(f"{ACCENT}{BOX_V}{RESET} {padded} {ACCENT}{BOX_V}{RESET}")

    return "\n".join([top, title_line, sep] + content_lines + [bottom])


def nika_banner() -> str:
    """Render the Nika startup banner."""
    logo = r"""
    ███╗   ██╗██╗██╗  ██╗ █████╗
    ████╗  ██║██║██║ ██╔╝██╔══██╗
    ██╔██╗ ██║██║█████╔╝ ███████║
    ██║╚██╗██║██║██╔═██╗ ██╔══██║
    ██║ ╚████║██║██║  ██╗██║  ██║
    ╚═╝  ╚═══╝╚═╝╚═╝  ╚═╝╚═╝  ╚═╝"""

    banner_lines = []
    for line in logo.strip().split("\n"):
        banner_lines.append(f"{HEADER}{line}{RESET}")

    subtitle = f"{MUTED}  Native Multi-Agent OS  {ACCENT}{DOT}{RESET} {MUTED}Persistent Memory  {ACCENT}{DOT}{RESET} {MUTED}Terminal-Native{RESET}"

    return "\n".join(banner_lines + ["", subtitle, ""])


def status_dot(state: str) -> str:
    """Return a colored status dot."""
    colors = {
        "running":   "\033[38;2;0;200;83m",    # green
        "pending":   "\033[38;2;255;193;7m",    # yellow
        "completed": "\033[38;2;250;70;22m",    # orange (nika)
        "failed":    "\033[38;2;244;67;54m",    # red
        "idle":      DIM_FG,
    }
    color = colors.get(state, DIM_FG)
    return f"{color}{DOT}{RESET}"
