import requests
import os
from PIL import Image, ImageDraw, ImageFont

USERNAME = "4ravind-b"
TOKEN = os.environ.get("GH_TOKEN", "")
headers = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github.v3+json"
} if TOKEN else {}

NEON_RED    = (255, 68, 68)
NEON_CYAN   = (0, 255, 255)
NEON_GREEN  = (57, 255, 20)
NEON_YELLOW = (255, 255, 0)
NEON_PINK   = (255, 0, 200)
NEON_BLUE   = (0, 180, 255)
DIM         = (80, 30, 30)
WHITE       = (200, 200, 200)
GRAY        = (120, 120, 140)
BG          = (0, 5, 16)

LANG_COLORS = [NEON_GREEN, NEON_CYAN, NEON_PINK, NEON_YELLOW, NEON_BLUE, NEON_RED]

def fetch_stats():
    user = requests.get(f"https://api.github.com/users/{USERNAME}", headers=headers).json()
    repos = requests.get(f"https://api.github.com/users/{USERNAME}/repos?per_page=100", headers=headers).json()

    stars = sum(r.get("stargazers_count", 0) for r in repos if isinstance(r, dict))
    forks = sum(r.get("forks_count", 0) for r in repos if isinstance(r, dict))

    # Languages by bytes
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

    # Commits from events
    events = requests.get(f"https://api.github.com/users/{USERNAME}/events?per_page=100", headers=headers).json()
    commits = sum(
        len(e.get("payload", {}).get("commits", []))
        for e in events if isinstance(e, dict) and e.get("type") == "PushEvent"
    )

    # PRs: open + closed + merged
    pr_open   = requests.get(f"https://api.github.com/search/issues?q=author:{USERNAME}+type:pr+state:open",   headers=headers).json().get("total_count", 0)
    pr_closed = requests.get(f"https://api.github.com/search/issues?q=author:{USERNAME}+type:pr+state:closed", headers=headers).json().get("total_count", 0)
    pr_merged = requests.get(f"https://api.github.com/search/issues?q=author:{USERNAME}+type:pr+is:merged",    headers=headers).json().get("total_count", 0)

    # Issues
    issues_open   = requests.get(f"https://api.github.com/search/issues?q=author:{USERNAME}+type:issue+state:open",   headers=headers).json().get("total_count", 0)
    issues_closed = requests.get(f"https://api.github.com/search/issues?q=author:{USERNAME}+type:issue+state:closed", headers=headers).json().get("total_count", 0)

    return {
        "followers":    user.get("followers", 0),
        "public_repos": user.get("public_repos", 0),
        "stars":        stars,
        "forks":        forks,
        "commits":      commits,
        "pr_open":      pr_open,
        "pr_closed":    pr_closed,
        "pr_merged":    pr_merged,
        "issues_open":  issues_open,
        "issues_closed":issues_closed,
        "lang_pct":     lang_pct,
    }

def glow_rect(d, x1, y1, x2, y2, color, glow_radius=4):
    for r in range(glow_radius, 0, -1):
        gc = tuple(min(255, int(c * 0.15)) for c in color)
        d.rectangle([x1-r, y1-r, x2+r, y2+r], fill=gc)
    d.rectangle([x1, y1, x2, y2], fill=color)

def glow_text(d, pos, text, color, font, radius=2):
    x, y = pos
    for dx in range(-radius, radius+1):
        for dy in range(-radius, radius+1):
            if dx == 0 and dy == 0:
                continue
            gc = tuple(min(255, int(c * 0.2)) for c in color)
            d.text((x+dx, y+dy), text, fill=gc, font=font)
    d.text((x, y), text, fill=color, font=font)

def divider(d, y, W, PAD, color=DIM):
    d.line([(PAD, y), (W - PAD, y)], fill=color, width=1)

def render_terminal(stats):
    W, H = 820, 620
    PAD = 36
    LINE = 25

    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    try:
        font      = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 14)
        font_sm   = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 12)
        font_bold = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 14)
    except:
        font = font_sm = font_bold = ImageFont.load_default()

    # Title bar
    d.rectangle([0, 0, W, 36], fill=(8, 8, 20))
    for i, col in enumerate([(255,95,86),(255,189,46),(39,201,63)]):
        cx = PAD + i * 22
        d.ellipse([cx, 11, cx+14, 25], fill=col)
    d.text((W//2 - 95, 10), "4ravind-b  ──  ~/terminal-stats", fill=(100,100,120), font=font_sm)

    # Scanlines
    for sy in range(36, H, 3):
        d.line([(0, sy), (W, sy)], fill=(0, 4, 12), width=1)

    y = 48

    def txt(text, color=WHITE, f=None):
        nonlocal y
        glow_text(d, (PAD, y), text, color, f or font)
        y += LINE

    def gap(px=10):
        nonlocal y
        y += px

    # Prompt 1
    txt("┌──(4ravind-b㉿kali)-[~]", NEON_RED, font_bold)
    txt("└─$ whoami --full", NEON_RED, font_bold)
    gap(6)
    divider(d, y, W, PAD, NEON_RED)
    gap(8)

    # Identity
    identity = [
        ("ENTITY",      "4ravind-b",                        NEON_RED),
        ("NAME",        "Aravind",                          WHITE),
        ("ROLE",        "Offensive Security Enthusiast",    NEON_CYAN),
        ("FOCUS",       "Web Exploitation  |  Red Team",    NEON_CYAN),
        ("ENVIRONMENT", "Kali Linux",                       NEON_GREEN),
        ("PATH",        "CEH -> eJPT -> OSCP -> Red Team",  NEON_YELLOW),
        ("STATUS",      "Breaking. Learning. Contributing.",NEON_PINK),
    ]
    for key, val, color in identity:
        glow_text(d, (PAD + 10, y), f"  {key.ljust(11)} : ", GRAY, font_sm)
        glow_text(d, (PAD + 160, y), val, color, font_bold)
        y += LINE - 2

    gap(8)
    divider(d, y, W, PAD, NEON_RED)
    gap(12)

    # Prompt 2
    txt("┌──(4ravind-b㉿kali)-[~]", NEON_RED, font_bold)
    txt("└─$ gh stat --user 4ravind-b", NEON_RED, font_bold)
    gap(8)

    # Two columns
    col1_x = PAD + 10
    col2_x = PAD + 360
    row_y = y

    # Stats column
    glow_text(d, (col1_x, row_y), "[ GITHUB STATS ]", NEON_RED, font_bold)
    ry = row_y + LINE + 2

    stats_rows = [
        ("Stars",         str(stats["stars"]),                          NEON_YELLOW),
        ("Forks",         str(stats["forks"]),                          WHITE),
        ("Followers",     str(stats["followers"]),                      WHITE),
        ("Repos",         str(stats["public_repos"]),                   WHITE),
        ("Commits(90d)",  str(stats["commits"]),                        NEON_GREEN),
        ("PRs Open",      str(stats["pr_open"]),                        NEON_CYAN),
        ("PRs Merged",    str(stats["pr_merged"]),                      NEON_GREEN),
        ("PRs Closed",    str(stats["pr_closed"]),                      WHITE),
        ("Issues Open",   str(stats["issues_open"]),                    NEON_PINK),
        ("Issues Closed", str(stats["issues_closed"]),                  GRAY),
    ]

    for label, val, color in stats_rows:
        glow_text(d, (col1_x, ry), f"  {label.ljust(14)}: ", GRAY, font_sm)
        glow_text(d, (col1_x + 210, ry), val, color, font_bold)
        ry += LINE - 3

    # Language bars column
    glow_text(d, (col2_x, row_y), "[ LANGUAGES ]", NEON_CYAN, font_bold)
    ry2 = row_y + LINE + 2
    bar_max_w = W - col2_x - PAD - 10
    BAR_H = 13

    for i, (lang, pct) in enumerate(stats["lang_pct"]):
        color = LANG_COLORS[i % len(LANG_COLORS)]
        bar_w = max(4, int(bar_max_w * pct / 100))
        glow_text(d, (col2_x, ry2), f"{lang[:10].ljust(10)}", color, font_sm)
        bx = col2_x + 108
        glow_rect(d, bx, ry2 + 2, bx + bar_w, ry2 + BAR_H, color, glow_radius=3)
        glow_text(d, (bx + bar_w + 6, ry2), f"{pct}%", color, font_sm)
        ry2 += LINE

    y = max(ry, ry2) + 12
    divider(d, y, W, PAD, DIM)
    y += 12

    txt("┌──(4ravind-b㉿kali)-[~]", NEON_RED, font_bold)
    txt("└─$ █", NEON_RED, font_bold)

    img.save("terminal_stats.png")
    print(f"Saved terminal_stats.png ({W}x{H})")

if __name__ == "__main__":
    stats = fetch_stats()
    render_terminal(stats)
