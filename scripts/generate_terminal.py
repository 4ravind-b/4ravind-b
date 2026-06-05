import requests
import os
from PIL import Image, ImageDraw, ImageFont

USERNAME = "4ravind-b"
TOKEN = os.environ.get("GH_TOKEN", "")
headers = {"Authorization": f"token {TOKEN}"} if TOKEN else {}

NEON_RED    = (255, 68, 68)
NEON_CYAN   = (0, 255, 255)
NEON_GREEN  = (57, 255, 20)
NEON_YELLOW = (255, 255, 0)
NEON_PINK   = (255, 0, 200)
NEON_BLUE   = (0, 180, 255)
DIM         = (80, 30, 30)
WHITE       = (200, 200, 200)
BG          = (0, 5, 16)

LANG_COLORS = [NEON_GREEN, NEON_CYAN, NEON_PINK, NEON_YELLOW, NEON_BLUE, NEON_RED]

def fetch_stats():
    user = requests.get(f"https://api.github.com/users/{USERNAME}", headers=headers).json()
    repos = requests.get(f"https://api.github.com/users/{USERNAME}/repos?per_page=100", headers=headers).json()

    stars = sum(r.get("stargazers_count", 0) for r in repos if isinstance(r, dict))
    forks = sum(r.get("forks_count", 0) for r in repos if isinstance(r, dict))

    lang_bytes = {}
    for repo in repos:
        if isinstance(repo, dict) and not repo.get("fork"):
            langs_url = repo.get("languages_url", "")
            if langs_url:
                lang_data = requests.get(langs_url, headers=headers).json()
                for lang, count in lang_data.items():
                    lang_bytes[lang] = lang_bytes.get(lang, 0) + count

    total_bytes = sum(lang_bytes.values()) or 1
    top_langs = sorted(lang_bytes.items(), key=lambda x: x[1], reverse=True)[:5]
    lang_pct = [(l, round(b / total_bytes * 100, 1)) for l, b in top_langs]

    events = requests.get(f"https://api.github.com/users/{USERNAME}/events?per_page=100", headers=headers).json()
    commits = sum(
        len(e.get("payload", {}).get("commits", []))
        for e in events if isinstance(e, dict) and e.get("type") == "PushEvent"
    )
    prs = requests.get(
        f"https://api.github.com/search/issues?q=author:{USERNAME}+type:pr", headers=headers
    ).json().get("total_count", 0)
    issues = requests.get(
        f"https://api.github.com/search/issues?q=author:{USERNAME}+type:issue", headers=headers
    ).json().get("total_count", 0)

    return {
        "followers": user.get("followers", 0),
        "public_repos": user.get("public_repos", 0),
        "stars": stars,
        "forks": forks,
        "commits": commits,
        "prs": prs,
        "issues": issues,
        "lang_pct": lang_pct,
    }

def glow_rect(d, x1, y1, x2, y2, color, glow_radius=4):
    for r in range(glow_radius, 0, -1):
        alpha = int(60 / r)
        gc = tuple(min(255, int(c * alpha / 60)) for c in color)
        d.rectangle([x1-r, y1-r, x2+r, y2+r], fill=gc)
    d.rectangle([x1, y1, x2, y2], fill=color)

def glow_text(d, pos, text, color, font, glow_radius=2):
    x, y = pos
    for dx in range(-glow_radius, glow_radius+1):
        for dy in range(-glow_radius, glow_radius+1):
            if dx == 0 and dy == 0:
                continue
            gc = tuple(min(255, int(c * 0.25)) for c in color)
            d.text((x+dx, y+dy), text, fill=gc, font=font)
    d.text((x, y), text, fill=color, font=font)

def render_terminal(stats):
    W, H = 800, 520
    PAD = 36

    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    try:
        font      = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 15)
        font_sm   = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 13)
        font_bold = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 15)
        font_lg   = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 17)
    except:
        font = font_sm = font_bold = font_lg = ImageFont.load_default()

    # Title bar background
    d.rectangle([0, 0, W, 38], fill=(10, 10, 20))
    for i, col in enumerate([(255,95,86),(255,189,46),(39,201,63)]):
        cx = PAD + i * 22
        d.ellipse([cx, 12, cx+14, 26], fill=col)
    d.text((W//2 - 90, 11), "4ravind-b  ──  ~/terminal-stats", fill=(100,100,120), font=font_sm)

    # Subtle scanlines
    for sy in range(38, H, 3):
        d.line([(0, sy), (W, sy)], fill=(0, 5, 10), width=1)

    LINE = 26
    y = 52

    def txt(text, color=WHITE, f=None, indent=0):
        nonlocal y
        glow_text(d, (PAD + indent, y), text, color, f or font)
        y += LINE

    def gap(n=1):
        nonlocal y
        y += LINE * n // 2

    # Prompt
    glow_text(d, (PAD, y), "┌──(4ravind-b㉿kali)-[~]", NEON_RED, font_bold)
    y += LINE
    glow_text(d, (PAD, y), "└─$ ", NEON_RED, font_bold)
    glow_text(d, (PAD + 40, y), "cat github_stats.conf", WHITE, font)
    y += LINE
    gap()

    # ── LEFT COLUMN: stats ──────────────────────────────
    col1_x = PAD + 10
    col2_x = PAD + 340
    row_y = y

    # Stats header
    glow_text(d, (col1_x, row_y), "[ GITHUB STATS ]", NEON_RED, font_bold)
    ry = row_y + LINE + 4

    stats_rows = [
        ("Stars",        str(stats["stars"]),       NEON_YELLOW),
        ("Forks",        str(stats["forks"]),        WHITE),
        ("Followers",    str(stats["followers"]),    WHITE),
        ("Repos",        str(stats["public_repos"]), WHITE),
        ("Commits(90d)", str(stats["commits"]),      NEON_GREEN),
        ("Pull Reqs",    str(stats["prs"]),          NEON_CYAN),
        ("Issues",       str(stats["issues"]),       NEON_PINK),
    ]

    for label, val, color in stats_rows:
        glow_text(d, (col1_x, ry), f"  {label.ljust(12)}: ", (120,120,140), font_sm)
        glow_text(d, (col1_x + 190, ry), val, color, font_bold)
        ry += LINE - 2

    # ── RIGHT COLUMN: language bars ─────────────────────
    glow_text(d, (col2_x, row_y), "[ LANGUAGES ]", NEON_CYAN, font_bold)
    ry2 = row_y + LINE + 4

    bar_max_w = W - col2_x - PAD - 10
    BAR_H = 14

    for i, (lang, pct) in enumerate(stats["lang_pct"]):
        color = LANG_COLORS[i % len(LANG_COLORS)]
        bar_w = max(4, int(bar_max_w * pct / 100))

        # lang name
        glow_text(d, (col2_x, ry2), f"{lang[:10].ljust(10)}", color, font_sm)

        # bar
        bx = col2_x + 108
        glow_rect(d, bx, ry2 + 1, bx + bar_w, ry2 + BAR_H, color, glow_radius=3)

        # pct label
        glow_text(d, (bx + bar_w + 6, ry2), f"{pct}%", color, font_sm)

        ry2 += LINE + 2

    y = max(ry, ry2) + LINE // 2

    # Bottom prompt
    gap()
    glow_text(d, (PAD, y), "┌──(4ravind-b㉿kali)-[~]", NEON_RED, font_bold)
    y += LINE
    glow_text(d, (PAD, y), "└─$ █", NEON_RED, font_bold)

    img.save("terminal_stats.png")
    print(f"Saved terminal_stats.png ({W}x{H})")

if __name__ == "__main__":
    stats = fetch_stats()
    render_terminal(stats)
