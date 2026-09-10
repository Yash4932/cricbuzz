"""
utils/theme.py
----------------
Injects the app's custom visual identity on top of Streamlit's default
styling: a dark, gradient-driven "sports broadcast" aesthetic (inspired by
the project brief's own mockup), glassmorphic cards, a gradient masthead,
an animated pulsing "LIVE" indicator, and subtle hover/entry animations.

Kept in one place so every page calls apply_theme() once and gets a
consistent look without repeating CSS.
"""

import streamlit as st


def _render_html(html: str) -> None:
    """
    Render a raw HTML/SVG block via st.markdown safely.

    Streamlit's markdown renderer treats 4+ leading spaces on a line as a
    CommonMark indented code block. Python's own indentation habits mean an
    f-string built inside a nested function often has 8-12 spaces of leading
    whitespace on every line -- normally harmless, but if a large *unindented*
    multi-line string (like an embedded SVG constant) gets interpolated in the
    middle of it, the parser's block-context resets partway through and the
    lines *after* the insertion can suddenly get treated as a code block
    instead of raw HTML. Stripping leading whitespace from every line before
    rendering sidesteps the whole class of bug.
    """
    dedented = "\n".join(line.lstrip() for line in html.strip("\n").split("\n"))
    st.markdown(dedented, unsafe_allow_html=True)


PREMIUM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@400;500;600&display=swap');

:root {
    /* Premium dark palette: near-black base, deep emerald + gold accents
       (pitch green + trophy gold) instead of the earlier pink/purple scheme. */
    --grad-1: #D4AF37;   /* gold */
    --grad-2: #12734A;   /* deep emerald */
    --grad-3: #081310;   /* near-black green */
    --accent: #E8C468;   /* warm gold highlight */
    --glass-bg: rgba(255, 255, 255, 0.045);
    --glass-border: rgba(212, 175, 55, 0.16);
    --success: #2FBF71;
    --live-red: #E5484D;
    --bg-base: #0A0D0C;
    --bg-mid: #0F1512;
}

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

h1, h2, h3, .hero-title {
    font-family: 'Space Grotesk', sans-serif !important;
}

/* ---------- App background: deep gradient wash + slow-drifting glow orbs ---------- */
.stApp {
    background: linear-gradient(180deg, var(--bg-base) 0%, var(--bg-mid) 50%, var(--bg-base) 100%);
    position: relative;
    overflow-x: hidden;
}
.stApp::before, .stApp::after {
    content: "";
    position: fixed;
    width: 60vw; height: 60vw;
    max-width: 900px; max-height: 900px;
    border-radius: 50%;
    filter: blur(90px);
    z-index: 0;
    pointer-events: none;
    opacity: 0.22;
}
.stApp::before {
    top: -15%; left: -10%;
    background: radial-gradient(circle, #12734A 0%, transparent 70%);
    animation: driftOne 22s ease-in-out infinite alternate;
}
.stApp::after {
    bottom: -20%; right: -10%;
    background: radial-gradient(circle, #D4AF37 0%, transparent 70%);
    animation: driftTwo 26s ease-in-out infinite alternate;
}
@keyframes driftOne {
    0%   { transform: translate(0, 0) scale(1); }
    100% { transform: translate(6vw, 8vh) scale(1.15); }
}
@keyframes driftTwo {
    0%   { transform: translate(0, 0) scale(1); }
    100% { transform: translate(-5vw, -6vh) scale(1.1); }
}
/* keep actual app content above the floating orbs */
.stApp > div:nth-child(1) { position: relative; z-index: 1; }
section[data-testid="stSidebar"] { position: relative; z-index: 2; }

/* ---------- Hero / masthead ---------- */
.hero-banner {
    padding: 2.3rem 2.5rem;
    border-radius: 22px;
    background: linear-gradient(115deg, var(--grad-1) 0%, var(--grad-2) 55%, var(--grad-3) 100%);
    background-size: 220% 220%;
    animation: fadeSlideIn 0.6s ease-out, gradientShift 12s ease-in-out infinite;
    box-shadow: 0 20px 50px -16px rgba(123,47,247,0.6), 0 0 0 1px rgba(255,255,255,0.06) inset;
    margin-bottom: 1.6rem;
    position: relative;
    overflow: hidden;
}
.hero-banner::after {
    content: "";
    position: absolute; inset: 0;
    background:
        radial-gradient(circle at 90% -10%, rgba(255,255,255,0.28), transparent 55%),
        radial-gradient(circle at 6% 8%, rgba(255,255,255,0.16), transparent 40%);
    pointer-events: none;
}
.hero-banner::before {
    content: "";
    position: absolute;
    top: 0; left: -60%;
    width: 45%; height: 100%;
    background: linear-gradient(115deg, transparent, rgba(255,255,255,0.16), transparent);
    transform: skewX(-18deg);
    animation: shimmerSweep 5s ease-in-out infinite;
    z-index: 1;
}
@keyframes gradientShift {
    0%   { background-position: 0% 50%; }
    50%  { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}
@keyframes shimmerSweep {
    0%   { left: -60%; }
    45%  { left: 130%; }
    100% { left: 130%; }
}
.hero-title {
    font-size: 2.15rem;
    font-weight: 700;
    color: white;
    margin: 0;
    letter-spacing: -0.02em;
    position: relative; z-index: 2;
}
.hero-tagline {
    color: rgba(255,255,255,0.9);
    font-size: 1.03rem;
    margin-top: 0.35rem;
    font-weight: 500;
    position: relative; z-index: 2;
}

/* ---------- Animated backdrop: falling cricket balls ---------- */
/* A soft rain of small glowing cricket-ball spheres drifts down behind the
   hero title on every page -- varied size/speed/blur per ball for a subtle
   depth-of-field feel. Purely decorative: no pointer events, low opacity,
   title text sits above it (z-index) so it stays fully legible. */
.hero-anim-wrap {
    position: absolute; inset: 0;
    overflow: hidden;
    pointer-events: none;
    border-radius: 22px;
    z-index: 0;
}
.falling-ball {
    position: absolute;
    top: -8%;
    border-radius: 50%;
    background: radial-gradient(circle at 32% 28%, #FFD9A0 0%, #E8542F 42%, #7A1F0E 100%);
    box-shadow: 0 0 10px rgba(232, 84, 47, 0.45);
    animation-name: fallDown;
    animation-timing-function: linear;
    animation-iteration-count: infinite;
}
.falling-ball::after {
    content: "";
    position: absolute; inset: 0;
    border-radius: 50%;
    background: linear-gradient(115deg, transparent 42%, rgba(255,255,255,0.35) 50%, transparent 58%);
}
@keyframes fallDown {
    0%   { transform: translateY(-20px) rotate(0deg); opacity: 0; }
    10%  { opacity: 1; }
    72%  { opacity: 1; }
    100% { transform: translateY(170px) rotate(360deg); opacity: 0; }
}

/* ---------- Glass cards ---------- */
.glass-card {
    background: var(--glass-bg);
    border: 1px solid var(--glass-border);
    border-radius: 18px;
    padding: 1.3rem 1.5rem;
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
    transition: transform 0.28s cubic-bezier(.22,1,.36,1), box-shadow 0.28s ease, border-color 0.28s ease, background 0.28s ease;
    animation: fadeSlideIn 0.55s cubic-bezier(.22,1,.36,1) both;
    position: relative;
}
.glass-card:hover {
    transform: translateY(-5px) scale(1.012);
    border-color: rgba(255,255,255,0.3);
    background: rgba(255,255,255,0.08);
    box-shadow: 0 18px 40px -16px rgba(123,47,247,0.45), 0 0 0 1px rgba(255,255,255,0.08) inset;
}
/* stagger successive cards on a page so they cascade in rather than pop together */
div[data-testid="column"]:nth-of-type(1) .glass-card { animation-delay: 0.02s; }
div[data-testid="column"]:nth-of-type(2) .glass-card { animation-delay: 0.12s; }

/* ---------- Signature motif: stitched-seam divider (cricket ball inspired) ---------- */
.seam-divider {
    display: flex; align-items: center; gap: 10px;
    margin: 1.4rem 0;
    opacity: 0.9;
}
.seam-divider::before, .seam-divider::after {
    content: "";
    flex: 1; height: 2px;
    background: repeating-linear-gradient(
        90deg,
        rgba(255,95,109,0.55) 0px, rgba(255,95,109,0.55) 6px,
        transparent 6px, transparent 12px
    );
    background-size: 200% 100%;
    animation: seamMove 3.5s linear infinite;
}
.seam-divider .seam-dot {
    width: 7px; height: 7px; border-radius: 50%;
    background: linear-gradient(135deg, var(--grad-1), var(--grad-2));
    box-shadow: 0 0 10px rgba(255,95,109,0.7);
    flex-shrink: 0;
}
@keyframes seamMove {
    0%   { background-position: 0% 0; }
    100% { background-position: -100% 0; }
}

/* ---------- Custom scrollbar ---------- */
::-webkit-scrollbar { width: 10px; height: 10px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb {
    background: linear-gradient(180deg, var(--grad-1), var(--grad-2));
    border-radius: 999px;
    border: 2px solid #0E0B1A;
}

/* ---------- Metric-style stat chip ---------- */
.stat-chip {
    display: flex; flex-direction: column; gap: 2px;
    padding: 1rem 1.15rem;
    border-radius: 14px;
    background: linear-gradient(135deg, rgba(255,95,109,0.14), rgba(123,47,247,0.14));
    border: 1px solid var(--glass-border);
    transition: transform 0.25s cubic-bezier(.22,1,.36,1), box-shadow 0.25s ease;
    animation: fadeSlideIn 0.5s cubic-bezier(.22,1,.36,1) both;
}
.stat-chip:hover {
    transform: translateY(-3px);
    box-shadow: 0 12px 28px -14px rgba(123,47,247,0.55);
}
.stat-chip .label { font-size: 0.78rem; color: rgba(255,255,255,0.65); font-weight: 500; text-transform: uppercase; letter-spacing: .04em;}
.stat-chip .value {
    font-size: 1.65rem; font-weight: 700; font-family: 'Space Grotesk', sans-serif;
    background: linear-gradient(120deg, #FFFFFF, #FFD9C0);
    -webkit-background-clip: text; background-clip: text; color: transparent;
}

/* ---------- Live pulse indicator ---------- */
.live-dot {
    display: inline-block; width: 9px; height: 9px; border-radius: 50%;
    background: var(--live-red);
    margin-right: 7px;
    box-shadow: 0 0 0 0 rgba(255,59,92, 0.7);
    animation: pulse 1.6s infinite;
    position: relative; top: -1px;
}
.live-badge {
    display: inline-flex; align-items: center;
    background: rgba(255,59,92,0.14);
    border: 1px solid rgba(255,59,92,0.4);
    color: #FF6B85;
    font-weight: 600; font-size: 0.78rem;
    padding: 3px 10px 3px 8px;
    border-radius: 999px;
    letter-spacing: 0.03em;
}
@keyframes pulse {
    0%   { box-shadow: 0 0 0 0 rgba(255,59,92,0.55); }
    70%  { box-shadow: 0 0 0 9px rgba(255,59,92,0); }
    100% { box-shadow: 0 0 0 0 rgba(255,59,92,0); }
}

/* ---------- Section fade-in ---------- */
@keyframes fadeSlideIn {
    from { opacity: 0; transform: translateY(10px); }
    to   { opacity: 1; transform: translateY(0); }
}
.section-anim { animation: fadeSlideIn 0.5s ease-out; }

/* ---------- Score bar (mini progress) ---------- */
.score-track {
    width: 100%; height: 7px; border-radius: 999px;
    background: rgba(255,255,255,0.08); overflow: hidden; margin-top: 6px;
}
.score-fill {
    height: 100%; border-radius: 999px;
    background: linear-gradient(90deg, var(--grad-1), var(--accent));
    transition: width 0.6s ease;
}

/* ---------- Sidebar polish ---------- */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #150F26 0%, #0E0B1A 100%);
    border-right: 1px solid rgba(255,255,255,0.06);
}

/* ---------- Pill / badge for level tags ---------- */
.level-pill {
    display: inline-block; padding: 2px 11px; border-radius: 999px;
    font-size: 0.74rem; font-weight: 600; letter-spacing: .03em;
}
.level-Beginner { background: rgba(62,213,152,0.14); color: #3ED598; border: 1px solid rgba(62,213,152,0.35);}
.level-Intermediate { background: rgba(255,179,71,0.14); color: #FFB347; border: 1px solid rgba(255,179,71,0.35);}
.level-Advanced { background: rgba(255,59,92,0.14); color: #FF6B85; border: 1px solid rgba(255,59,92,0.35);}

/* ---------- Buttons ---------- */
.stButton>button, .stFormSubmitButton>button {
    background: linear-gradient(120deg, var(--grad-1) 0%, var(--grad-2) 50%, var(--grad-1) 100%);
    background-size: 220% 100%;
    color: white; border: none; border-radius: 10px; font-weight: 600;
    transition: transform 0.18s ease, box-shadow 0.18s ease, background-position 0.5s ease;
}
.stButton>button:hover, .stFormSubmitButton>button:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 24px -8px rgba(123,47,247,0.7);
    background-position: 100% 0;
}
.stButton>button:active, .stFormSubmitButton>button:active {
    transform: translateY(0px) scale(0.98);
}

/* ---------- Sidebar nav polish ---------- */
section[data-testid="stSidebar"] a[data-testid="stSidebarNavLink"] {
    border-radius: 10px;
    padding-top: 9px;
    padding-bottom: 9px;
    transition: background 0.2s ease, padding-left 0.2s ease;
}
section[data-testid="stSidebar"] a[data-testid="stSidebarNavLink"] p {
    font-size: 1.08rem !important;
    font-weight: 600 !important;
    letter-spacing: -0.01em;
}
section[data-testid="stSidebar"] a[data-testid="stSidebarNavLink"] [data-testid="stIconEmoji"] {
    font-size: 1.15rem !important;
}
section[data-testid="stSidebar"] a[data-testid="stSidebarNavLink"]:hover {
    background: rgba(255,255,255,0.07);
    padding-left: 6px;
}
section[data-testid="stSidebar"] [data-testid="stNavSectionHeader"] p {
    font-size: 0.85rem !important;
    font-weight: 700 !important;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    opacity: 0.65;
}

/* ---------- Tables ---------- */
[data-testid="stDataFrame"] {
    border-radius: 14px; overflow: hidden;
    border: 1px solid var(--glass-border);
}

/* ---------- Divider ---------- */
.thin-divider {
    height: 1px; width: 100%;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.18), transparent);
    margin: 1.1rem 0;
}
</style>
"""


def apply_theme():
    st.markdown(PREMIUM_CSS, unsafe_allow_html=True)


def _build_falling_balls_html() -> str:
    """
    Generates a fixed (but visually varied) set of falling-ball divs: spread
    across the width, with different sizes/speeds/delays/blur so they read
    as an organic drift rather than a mechanical, synchronized rain.
    Deterministic (no randomness) so output is stable across reruns.
    """
    # (left%, size_px, duration_s, delay_s, blur_px)
    balls = [
        (4,  10, 6.5, -1.2, 0.5),
        (11, 16, 5.2, -3.6, 0),
        (18, 8,  7.8, -0.4, 1),
        (25, 13, 6.0, -4.8, 0.3),
        (33, 19, 5.6, -2.1, 0),
        (40, 9,  7.2, -5.5, 0.8),
        (47, 15, 6.4, -0.9, 0),
        (54, 11, 8.1, -3.3, 0.6),
        (61, 17, 5.4, -6.2, 0),
        (68, 8,  6.9, -1.7, 1),
        (75, 14, 7.5, -4.1, 0.3),
        (82, 20, 5.0, -2.6, 0),
        (89, 10, 6.7, -5.9, 0.6),
        (95, 12, 7.0, -0.6, 0.4),
        (58, 7,  8.4, -3.9, 1),
        (29, 16, 6.1, -1.4, 0),
    ]
    divs = []
    for left, size, duration, delay, blur in balls:
        style = (
            f"left:{left}%; width:{size}px; height:{size}px; "
            f"animation-duration:{duration}s; animation-delay:{delay}s; "
            f"filter: blur({blur}px);"
        )
        divs.append(f'<div class="falling-ball" style="{style}"></div>')
    return "\n".join(divs)


_FALLING_BALLS_SCENE = f"""
<div class="hero-anim-wrap">
{_build_falling_balls_html()}
</div>
"""



def hero_banner(title: str, tagline: str, icon: str = "🏏"):
    _render_html(
        f"""
        <div class="hero-banner">
            {_FALLING_BALLS_SCENE}
            <div class="hero-title">{icon} {title}</div>
            <div class="hero-tagline">{tagline}</div>
        </div>
        """
    )


def stat_chip(label: str, value):
    _render_html(
        f"""
        <div class="stat-chip">
            <div class="label">{label}</div>
            <div class="value">{value}</div>
        </div>
        """
    )


def live_badge(text: str = "LIVE"):
    _render_html(f'<span class="live-badge"><span class="live-dot"></span>{text}</span>')


def level_pill(level: str):
    _render_html(f'<span class="level-pill level-{level}">{level}</span>')


def thin_divider():
    _render_html('<div class="thin-divider"></div>')


def seam_divider():
    """A stitched-seam style divider (cricket ball motif) — the app's signature accent."""
    _render_html('<div class="seam-divider"><span></span><span class="seam-dot"></span><span></span></div>')
