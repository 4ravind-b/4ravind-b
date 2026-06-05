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
NEON_BLUE   = (0, 149, 255)
DIM         = (100, 40, 40)
WHITE       = (210, 210, 210)
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

def neon_text(d, pos, text, color, font):
    x, y = pos
    # glow effect: draw same text slightly offset in dim color
    for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
        glow = tuple(min(255, int(c * 0.3)) for c in color)
        d.text((x+dx, y+dy), text, fill=glow, font=font)
    d.text((x, y), text, fill=color, font=font)

def render_terminal(stats):
    W, H = 760, 500
    PAD = 32
    LINE = 24
    BAR_H = 14

    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 14)
        font_sm = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 12)
        font_bold = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 14)
    except:
        font = ImageFont.load_default()
        font_sm = font
        font_bold = font

    # Title bar
    for i, col in enumerate([(255,95,86),(255,189,46),(39,201,63)]):
        d.ellipse([PAD + i*22, 16, PAD + i*22 + 12, 28], fill=col)
    d.text((W//2 - 80, 13), "4ravind-b  —  terminal stats", fill=(130,130,130), font=font_sm)

    # Scanline effect
    for sy in range(0, H, 4):
        d.line([(0, sy), (W, sy)], fill=(0, 0, 0, 30), width=1)

    y = 48

    def line(text, color=WHITE, f=None):
        nonlocal y
        neon_text(d, (PAD, y), text, color, f or font)
        y += LINE

    def blank():
        nonlocal y
        y += LINE // 2

    line("┌──(4ravind-b㉿kali)-[~]", NEON_RED, font_bold)
    line("└─$ gh api stats --user 4ravind-b", NEON_RED)
    blank()

    # Stats box
    box_x = PAD + 10
    box_w = 320
    line("  ┌─────────────────────────────┐", DIM)
    line("  │      GITHUB  STATS          │", NEON_RED, font_bold)
    line("  ├─────────────────────────────┤", DIM)
    line(f"  │  Stars         : {str(stats['stars']).ljust(11)}│", WHITE)
    line(f"  │  Forks         : {str(stats['forks']).ljust(11)}│", WHITE)
    line(f"  │  Followers     : {str(stats['followers']).ljust(11)}│", WHITE)
    line(f"  │  Public Repos  : {str(stats['public_repos']).ljust(11)}│", WHITE)
    line(f"  │  Commits (90d) : {str(stats['commits']).ljust(11)}│", NEON_GREEN)
    line(f"  │  Pull Requests : {str(stats['prs']).ljust(11)}│", NEON_CYAN)
    line(f"  │  Issues        : {str(stats['issues']).ljust(11)}│", NEON_YELLOW)
    line("  └─────────────────────────────┘", DIM)

    blank()
    line("  LANGUAGES BY USAGE", NEON_CYAN, font_bold)
    blank()

    # Language bars with neon glow
    bar_x = PAD + 10
    bar_max_w = W - bar_x - PAD - 80

    for i, (lang, pct) in enumerate(stats["lang_pct"]):
        color = LANG_COLORS[i % len(LANG_COLORS)]
        bar_w = int(bar_max_w * pct / 100)

        # label
        label = f"  {lang[:12].ljust(12)}"
        d.text((bar_x, y), label, fill=color, font=font_sm)

        # neon bar
        bx = bar_x + 110
        # glow layers
        for gw in [6, 4, 2]:
            glow_color = tuple(min(255, int(c * 0.2)) for c in color)
            d.rectangle([bx, y - gw//2, bx + bar_w, y + BAR_H + gw//2], fill=glow_color)
        d.rectangle([bx, y, bx + bar_w, y + BAR_H], fill=color)

        # percentage
        d.text((bx + bar_w + 8, y), f"{pct}%", fill=color, font=font_sm)

        y += LINE + 4

    blank()
    line("┌──(4ravind-b㉿kali)-[~]", NEON_RED, font_bold)
    line("└─$ █", NEON_RED)

    img.save("terminal_stats.png")
    print("terminal_stats.png generated")

if __name__ == "__main__":
    stats = fetch_stats()
    render_terminal(stats)
