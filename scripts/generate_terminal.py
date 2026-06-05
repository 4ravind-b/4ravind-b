import requests
import os
from PIL import Image, ImageDraw, ImageFont
import textwrap

# GitHub API
USERNAME = "4ravind-b"
TOKEN = os.environ.get("GH_TOKEN", "")

headers = {"Authorization": f"token {TOKEN}"} if TOKEN else {}

def fetch_stats():
    # User info
    user = requests.get(f"https://api.github.com/users/{USERNAME}", headers=headers).json()
    
    # Repos
    repos = requests.get(f"https://api.github.com/users/{USERNAME}/repos?per_page=100", headers=headers).json()
    
    stars = sum(r.get("stargazers_count", 0) for r in repos if isinstance(r, dict))
    forks = sum(r.get("forks_count", 0) for r in repos if isinstance(r, dict))
    
    # Languages
    lang_count = {}
    for repo in repos:
        if isinstance(repo, dict) and repo.get("language"):
            lang = repo["language"]
            lang_count[lang] = lang_count.get(lang, 0) + 1
    top_langs = sorted(lang_count.items(), key=lambda x: x[1], reverse=True)[:3]

    # Events for commits
    events = requests.get(f"https://api.github.com/users/{USERNAME}/events?per_page=100", headers=headers).json()
    commits = sum(
        len(e.get("payload", {}).get("commits", []))
        for e in events if isinstance(e, dict) and e.get("type") == "PushEvent"
    )

    prs = requests.get(
        f"https://api.github.com/search/issues?q=author:{USERNAME}+type:pr",
        headers=headers
    ).json().get("total_count", 0)

    issues = requests.get(
        f"https://api.github.com/search/issues?q=author:{USERNAME}+type:issue",
        headers=headers
    ).json().get("total_count", 0)

    return {
        "followers": user.get("followers", 0),
        "public_repos": user.get("public_repos", 0),
        "stars": stars,
        "forks": forks,
        "commits": commits,
        "prs": prs,
        "issues": issues,
        "top_langs": top_langs,
    }

def render_terminal(stats):
    BG      = (0, 5, 16)
    GREEN   = (255, 68, 68)   # using red as accent to match theme
    DIM     = (138, 58, 58)
    WHITE   = (200, 200, 200)
    PROMPT  = (255, 68, 68)
    CYAN    = (255, 100, 100)

    W, H = 720, 420
    PAD = 28
    LINE = 22

    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    # Title bar dots
    for i, col in enumerate([(255,95,86),(255,189,46),(39,201,63)]):
        d.ellipse([PAD + i*22, 18, PAD + i*22 + 12, 30], fill=col)
    d.text((W//2 - 60, 14), "terminal — 4ravind-b", fill=(120,120,120))

    y = 52

    def line(text, color=WHITE):
        nonlocal y
        d.text((PAD, y), text, fill=color)
        y += LINE

    line(f"┌──(4ravind-b㉿kali)-[~]", GREEN)
    line(f"└─$ gh stat --user {USERNAME}", GREEN)
    line("")
    line(f"  ╔══════════════════════════════════════╗", DIM)
    line(f"  ║         GITHUB STATS                 ║", GREEN)
    line(f"  ╠══════════════════════════════════════╣", DIM)
    line(f"  ║  Stars         : {str(stats['stars']).ljust(20)}║", WHITE)
    line(f"  ║  Forks         : {str(stats['forks']).ljust(20)}║", WHITE)
    line(f"  ║  Followers     : {str(stats['followers']).ljust(20)}║", WHITE)
    line(f"  ║  Public Repos  : {str(stats['public_repos']).ljust(20)}║", WHITE)
    line(f"  ║  Commits (90d) : {str(stats['commits']).ljust(20)}║", WHITE)
    line(f"  ║  Pull Requests : {str(stats['prs']).ljust(20)}║", WHITE)
    line(f"  ║  Issues        : {str(stats['issues']).ljust(20)}║", WHITE)
    line(f"  ╠══════════════════════════════════════╣", DIM)

    langs_str = "  ".join(f"{l}({c})" for l,c in stats['top_langs'])
    line(f"  ║  Top Languages : {langs_str.ljust(20)}║", CYAN)
    line(f"  ╚══════════════════════════════════════╝", DIM)
    line("")
    line(f"┌──(4ravind-b㉿kali)-[~]", GREEN)
    line(f"└─$ █", GREEN)

    img.save("terminal_stats.png")
    print("terminal_stats.png generated")

if __name__ == "__main__":
    stats = fetch_stats()
    render_terminal(stats)
