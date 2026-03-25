"""LifeClaw theme system - 5 built-in themes for terminal and web."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Theme:
    name: str
    slug: str
    # Terminal colors (Rich markup compatible)
    primary: str
    secondary: str
    accent: str
    bg: str
    text: str
    muted: str
    success: str
    error: str
    warning: str
    info: str
    # Prompt colors
    prompt_user: str
    prompt_ai: str
    # Web CSS variables (hex)
    web_primary: str
    web_secondary: str
    web_accent: str
    web_bg: str
    web_surface: str
    web_text: str
    web_muted: str


AURORA = Theme(
    name="Aurora",
    slug="aurora",
    primary="#F4A261",       # light orange
    secondary="#B48EAD",     # light purple
    accent="#81A1C1",        # light blue
    bg="#2E3440",
    text="#ECEFF4",
    muted="#4C566A",
    success="#A3BE8C",
    error="#BF616A",
    warning="#EBCB8B",
    info="#88C0D0",
    prompt_user="bold #F4A261",
    prompt_ai="bold #B48EAD",
    web_primary="#F4A261",
    web_secondary="#B48EAD",
    web_accent="#81A1C1",
    web_bg="#1a1a2e",
    web_surface="#2E3440",
    web_text="#ECEFF4",
    web_muted="#4C566A",
)

MIDNIGHT = Theme(
    name="Midnight",
    slug="midnight",
    primary="#7C3AED",
    secondary="#06B6D4",
    accent="#F43F5E",
    bg="#0F172A",
    text="#F8FAFC",
    muted="#475569",
    success="#22C55E",
    error="#EF4444",
    warning="#F59E0B",
    info="#3B82F6",
    prompt_user="bold #7C3AED",
    prompt_ai="bold #06B6D4",
    web_primary="#7C3AED",
    web_secondary="#06B6D4",
    web_accent="#F43F5E",
    web_bg="#0F172A",
    web_surface="#1E293B",
    web_text="#F8FAFC",
    web_muted="#475569",
)

FOREST = Theme(
    name="Forest",
    slug="forest",
    primary="#4ADE80",
    secondary="#A78BFA",
    accent="#FCD34D",
    bg="#1A2E1A",
    text="#E8F5E8",
    muted="#3D5A3D",
    success="#86EFAC",
    error="#F87171",
    warning="#FDE68A",
    info="#67E8F9",
    prompt_user="bold #4ADE80",
    prompt_ai="bold #A78BFA",
    web_primary="#4ADE80",
    web_secondary="#A78BFA",
    web_accent="#FCD34D",
    web_bg="#1A2E1A",
    web_surface="#2D4A2D",
    web_text="#E8F5E8",
    web_muted="#3D5A3D",
)

OCEAN = Theme(
    name="Ocean",
    slug="ocean",
    primary="#22D3EE",
    secondary="#818CF8",
    accent="#FB923C",
    bg="#0C1222",
    text="#E0F2FE",
    muted="#1E3A5F",
    success="#34D399",
    error="#FB7185",
    warning="#FBBF24",
    info="#60A5FA",
    prompt_user="bold #22D3EE",
    prompt_ai="bold #818CF8",
    web_primary="#22D3EE",
    web_secondary="#818CF8",
    web_accent="#FB923C",
    web_bg="#0C1222",
    web_surface="#1E293B",
    web_text="#E0F2FE",
    web_muted="#1E3A5F",
)

MONOCHROME = Theme(
    name="Monochrome",
    slug="monochrome",
    primary="#E5E5E5",
    secondary="#A3A3A3",
    accent="#F5F5F5",
    bg="#171717",
    text="#FAFAFA",
    muted="#525252",
    success="#86EFAC",
    error="#FCA5A5",
    warning="#FDE68A",
    info="#BAE6FD",
    prompt_user="bold #E5E5E5",
    prompt_ai="bold #A3A3A3",
    web_primary="#E5E5E5",
    web_secondary="#A3A3A3",
    web_accent="#F5F5F5",
    web_bg="#171717",
    web_surface="#262626",
    web_text="#FAFAFA",
    web_muted="#525252",
)

ALL_THEMES: dict[str, Theme] = {
    "aurora": AURORA,
    "midnight": MIDNIGHT,
    "forest": FOREST,
    "ocean": OCEAN,
    "monochrome": MONOCHROME,
}

DEFAULT_THEME = "aurora"


def get_theme(name: str | None = None) -> Theme:
    return ALL_THEMES.get(name or DEFAULT_THEME, AURORA)
