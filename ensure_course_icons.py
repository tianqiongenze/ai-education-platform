#!/usr/bin/env python3
"""
ensure_course_icons.py — 新课程图标自愈脚本

对 Studio 中每一门课程:
  1. 若 course.course_image 为空 → 自动生成一枚与课程编号/主题相关的 PNG 图标
  2. 若 course_image 已设置但 asset 在 contentstore 中不存在 → 重新生成
  3. 否则跳过 (不动已有图标)

设计为在 CMS pod 内运行: kubectl exec <cms-pod> -- python3 /tmp/ensure_icons.py
也可以用 CronJob 直接在 cms 容器里执行, 无需额外镜像。
"""
import os
import sys
import zlib
import struct

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cms.envs.tutor.production")
sys.path.insert(0, "/openedx/edx-platform")
django.setup()

from opaque_keys.edx.locations import CourseLocator  # noqa: E402
from opaque_keys.edx.locator import AssetLocator  # noqa: E402
from opaque_keys.edx.keys import CourseKey  # noqa: E402
from xmodule.contentstore.content import StaticContent  # noqa: E402
from xmodule.contentstore.django import contentstore  # noqa: E402
from xmodule.modulestore.django import modulestore  # noqa: E402
from django.contrib.auth.models import User  # noqa: E402

# ---------------------------------------------------------------------------
# 图标生成: 纯 Python PNG 编码 (无第三方依赖)
# ---------------------------------------------------------------------------

def make_png(width, height, pixels):
    """pixels: list of rows, each row list of (r,g,b) tuples"""
    raw = b""
    for row in pixels:
        raw += b"\x00" + b"".join(struct.pack("BBB", *px) for px in row)

    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        c += struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        return c

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


def _glyph_pixels(glyph):
    """返回 (宽度, 行列表), 行中 1 = 前景色"""
    def rows(*lines):
        w = max(len(l) for l in lines)
        return w, [[1 if ch == "#" else 0 for ch in l.ljust(w)] for l in lines]

    if glyph == "code":
        return rows(
            "  ####    ",
            " #       ",
            "  #      ",
            "   ####  ",
        )
    if glyph == "tree":
        return rows(
            "   #   ",
            "  ###  ",
            " ##### ",
            "   #   ",
            "  ###  ",
        )
    if glyph == "globe":
        return rows(
            " ##### ",
            "#  #  #",
            "# ### #",
            "#  #  #",
            " ##### ",
        )
    if glyph == "plot":
        return rows(
            "       #",
            "     # #",
            "   #   #",
            " #     #",
            "########",
        )
    if glyph == "rocket":
        return rows(
            "   #   ",
            "  ###  ",
            " ##### ",
            "  ###  ",
            " #   # ",
        )
    if glyph == "brain":
        return rows(
            " ## ## ",
            "#######",
            " ## ## ",
            "#######",
            " ## ## ",
        )
    if glyph == "chart":
        return rows(
            "     # #",
            "   # # #",
            "   # # #",
            " # # # #",
            "########",
        )
    if glyph == "net":
        return rows(
            "#  #  #",
            " # # # ",
            "  ###  ",
            " # # # ",
            "#  #  #",
        )
    if glyph == "chat":
        return rows(
            "#######",
            "#     #",
            "# ### #",
            "#     #",
            "#######",
            "  # #  ",
        )
    if glyph == "game":
        return rows(
            "# # # #",
            "       ",
            "# # # #",
            "#######",
            "  # #  ",
        )
    if glyph == "cloud":
        return rows(
            "  #### ",
            " ##  ##",
            "#######",
            "#######",
            "  #### ",
        )
    if glyph == "eye":
        return rows(
            "  ####  ",
            " #    # ",
            "#  ##  #",
            " #    # ",
            "  ####  ",
        )
    if glyph == "db":
        return rows(
            "#######",
            "#     #",
            "#######",
            "#     #",
            "#######",
        )
    if glyph == "robot":
        return rows(
            "  ###  ",
            " ##### ",
            " # # # ",
            " ##### ",
            " #   # ",
        )
    if glyph == "shield":
        return rows(
            "#######",
            "#     #",
            "#  #  #",
            " ## ## ",
            "   #   ",
        )
    # 默认: 书本 (任何未知主题都有合理图标)
    return rows(
        "#######",
        "# ##  #",
        "# ##  #",
        "#     #",
        "#######",
    )


# 主题关键词 → (glyph, RGB)。按课程 key / 名称里出现的关键词匹配。
THEME_RULES = [
    (("python", "py", "编程", "code", "programming"), ("code", (46, 109, 183))),
    (("java",), ("code", (36, 140, 90))),
    (("go", "golang"), ("code", (40, 110, 140))),
    (("rust",), ("code", (190, 70, 70))),
    (("数据结构", "algorithm", "算法", "tree"), ("tree", (40, 110, 140))),
    (("web", "网络", "network", "互联网"), ("globe", (70, 130, 60))),
    (("数据分析", "data", "统计", "statistics", "可视化"), ("plot", (180, 110, 50))),
    (("机器学习", "ml", "machine", "深度学习", "ai", "人工智能"), ("brain", (108, 74, 182))),
    (("数据库", "database", "sql", "db"), ("db", (140, 110, 30))),
    (("安全", "security", "密码"), ("shield", (100, 60, 60))),
    (("游戏", "game"), ("game", (120, 50, 160))),
    (("云", "cloud", "devops", "docker", "k8s", "kubernetes"), ("cloud", (60, 100, 120))),
    (("聊天", "chat", "nlp", "语言"), ("chat", (30, 120, 150))),
    (("机器人", "robot"), ("robot", (60, 80, 180))),
    (("图", "graph", "分布式"), ("net", (170, 50, 90))),
    (("前端", "frontend", "ui"), ("chart", (200, 90, 40))),
]
DEFAULT_THEME = ("eye", (90, 90, 100))


def pick_theme(course_key_str, display_name):
    text = ("%s %s" % (course_key_str, display_name or "")).lower()
    for keywords, theme in THEME_RULES:
        for kw in keywords:
            if kw in text:
                return theme
    return DEFAULT_THEME


def draw_icon(glyph, rgb, size=480):
    """按 glyph 绘制图标: 纯色背景 + 圆角感白/浅色前景符号"""
    r, g, b = rgb
    bg = (r, g, b)
    fg = (255, 255, 255)
    accent = (min(255, r + 40), min(255, g + 40), min(255, b + 40))

    gw, grows = _glyph_pixels(glyph)
    gh = len(grows)
    pad_ratio = 0.18
    cell = int(size * (1 - 2 * pad_ratio) / max(gw, gh))
    ox = int((size - gw * cell) / 2)
    oy = int((size - gh * cell) / 2)

    px = [[bg for _ in range(size)] for _ in range(size)]

    # 顶部装饰条 (accent)
    for x in range(size):
        for y in range(int(size * 0.035)):
            px[y][x] = accent

    # 光晕: 左上略亮
    for y in range(size):
        for x in range(size):
            k = int(18 * (1 - (x + y) / (2 * size)))
            if k:
                pr, pg, pb = px[y][x]
                px[y][x] = (min(255, pr + k), min(255, pg + k), min(255, pb + k))

    # 前景符号
    for gy in range(gh):
        for gx in range(gw):
            if grows[gy][gx]:
                y0 = oy + gy * cell
                x0 = ox + gx * cell
                for yy in range(y0, min(size, y0 + cell)):
                    for xx in range(x0, min(size, x0 + cell)):
                        px[yy][xx] = fg
    return make_png(size, size, px)


# ---------------------------------------------------------------------------
# 主逻辑: 遍历课程, 补缺失图标
# ---------------------------------------------------------------------------

def ensure_icons(dry_run=False):
    ms = modulestore()
    cs = contentstore()
    uid = User.objects.filter(is_superuser=True).order_by("id").first()
    if uid is None:
        uid = User.objects.filter(is_staff=True).order_by("id").first()
    assert uid is not None, "no admin user found"

    fixed, skipped = [], []
    for course in ms.get_courses():
        ck = course.id
        # 只处理该课程所在 org (不处理 library)
        if not hasattr(ck, "org"):
            continue
        fname = getattr(course, "course_image", None)
        need_new = not fname
        if not need_new:
            # 检查 asset 是否真实存在
            try:
                loc = AssetLocator(ck.for_branch(None), "asset", fname)
                cs.find(loc)
            except Exception:
                need_new = True

        if not need_new:
            skipped.append(str(ck))
            continue

        key_str = str(ck)
        glyph, rgb = pick_theme(key_str, getattr(course, "display_name", ""))
        png = draw_icon(glyph, rgb)

        if not fname:
            # 课程号小写作为文件名, 保证 org+num+run 唯一性
            fname = "%s_course_image.png" % ck.course.lower()

        loc = AssetLocator(ck.for_branch(None), "asset", fname)
        content = StaticContent(loc, fname, "image/png", png)
        cs.save(content)

        course.course_image = fname
        course.banner_image = fname
        course.thumbnail_image = fname
        course.hero_image = fname
        if not dry_run:
            ms.update_item(course, uid.id)
        fixed.append((key_str, fname, glyph))
        print("FIXED  %s -> %s (glyph=%s)" % (key_str, fname, glyph))

    print("\nSummary: %d fixed, %d already-ok" % (len(fixed), len(skipped)))
    return fixed


if __name__ == "__main__":
    ensure_icons(dry_run="--dry-run" in sys.argv)
