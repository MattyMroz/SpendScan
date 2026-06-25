from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT_DIR = Path(__file__).resolve().parent / "figures"
OUT_DIR.mkdir(exist_ok=True)

W, H = 1400, 820


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            pass
    return ImageFont.load_default()


def rounded(draw, xy, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def text(draw, xy, value, size=24, fill="#111827", bold=False, anchor=None):
    draw.text(xy, value, font=font(size, bold), fill=fill, anchor=anchor)


def base(title: str, subtitle: str):
    img = Image.new("RGB", (W, H), "#f8fafc")
    d = ImageDraw.Draw(img)

    text(d, (56, 42), title, 36, "#111827", True)
    text(d, (56, 88), subtitle, 20, "#64748b")

    # Browser / app frame
    rounded(d, (56, 130, W - 56, H - 56), 26, "#ffffff", "#d7dee8", 2)
    rounded(d, (56, 130, W - 56, 196), 26, "#edf3f8", "#d7dee8", 2)
    d.rectangle((58, 168, W - 58, 196), fill="#edf3f8")
    for i, color in enumerate(["#ef4444", "#f59e0b", "#22c55e"]):
        d.ellipse((88 + i * 34, 154, 106 + i * 34, 172), fill=color)
    rounded(d, (210, 148, W - 110, 178), 14, "#ffffff", "#d7dee8", 1)
    text(d, (238, 154), "spendscan.local", 15, "#94a3b8")

    return img, d


def draw_sidebar(d):
    rounded(d, (86, 224, 290, 730), 18, "#102a43")
    text(d, (116, 254), "SpendScan", 25, "#ffffff", True)
    items = ["Skanuj", "Paragony", "Statystyki", "Kalendarz", "Ustawienia"]
    for i, item in enumerate(items):
        y = 320 + i * 64
        fill = "#1d4ed8" if i == 0 else "#173b5c"
        rounded(d, (112, y, 264, y + 42), 12, fill)
        text(d, (132, y + 11), item, 17, "#ffffff")


def scan_placeholder():
    img, d = base("Rys. 2. Ekran skanowania paragonu", "Miejsce na docelowy zrzut ekranu z aplikacji")
    draw_sidebar(d)

    text(d, (340, 238), "Dodaj paragon", 32, "#111827", True)
    text(d, (340, 282), "Prześlij jedno lub kilka zdjęć tego samego paragonu.", 19, "#64748b")

    rounded(d, (340, 330, 1280, 596), 22, "#f8fafc", "#cbd5e1", 2)
    d.line((384, 476, 1236, 476), fill="#cbd5e1", width=3)
    d.line((810, 374, 810, 552), fill="#cbd5e1", width=3)
    text(d, (810, 390), "Upuść zdjęcia tutaj", 29, "#334155", True, "ma")
    text(d, (810, 434), "JPG, PNG lub WEBP", 19, "#64748b", False, "ma")
    rounded(d, (668, 506, 952, 560), 14, "#2563eb")
    text(d, (810, 520), "Wybierz pliki", 20, "#ffffff", True, "ma")

    rounded(d, (340, 628, 610, 704), 16, "#eff6ff", "#bfdbfe", 1)
    text(d, (368, 648), "1", 18, "#1d4ed8", True)
    text(d, (402, 646), "OCR po stronie serwera", 18, "#1e293b", True)
    text(d, (402, 674), "bez zewnętrznej usługi OCR", 15, "#64748b")

    rounded(d, (636, 628, 906, 704), 16, "#f0fdf4", "#bbf7d0", 1)
    text(d, (664, 648), "2", 18, "#15803d", True)
    text(d, (698, 646), "Strukturyzacja Gemini", 18, "#1e293b", True)
    text(d, (698, 674), "pozycje, sumy i kategorie", 15, "#64748b")

    rounded(d, (932, 628, 1202, 704), 16, "#fff7ed", "#fed7aa", 1)
    text(d, (960, 648), "3", 18, "#c2410c", True)
    text(d, (994, 646), "Edycja przed zapisem", 18, "#1e293b", True)
    text(d, (994, 674), "użytkownik kontroluje wynik", 15, "#64748b")

    img.save(OUT_DIR / "rys-02-skanowanie-placeholder.png", quality=95)


def edit_placeholder():
    img, d = base("Rys. 3. Ekran edycji paragonu", "Miejsce na docelowy zrzut ekranu z aplikacji")
    draw_sidebar(d)

    text(d, (340, 238), "Edycja wyniku OCR", 32, "#111827", True)
    text(d, (340, 282), "Użytkownik może poprawić sklep, datę, pozycje i kwoty przed zapisem.", 19, "#64748b")

    rounded(d, (340, 326, 740, 710), 18, "#ffffff", "#d7dee8", 2)
    text(d, (374, 360), "Dane paragonu", 23, "#111827", True)
    labels = ["Sklep", "Data", "Suma", "Metoda płatności"]
    values = ["Biedronka", "2026-06-24", "83,47 PLN", "karta"]
    for i, (label, value) in enumerate(zip(labels, values, strict=False)):
        y = 414 + i * 66
        text(d, (374, y), label, 15, "#64748b")
        rounded(d, (374, y + 24, 704, y + 58), 8, "#f8fafc", "#cbd5e1", 1)
        text(d, (390, y + 31), value, 16, "#111827")

    rounded(d, (775, 326, 1280, 710), 18, "#ffffff", "#d7dee8", 2)
    text(d, (810, 360), "Pozycje", 23, "#111827", True)
    rows = [
        ("Chleb pszenny", "1", "4,99"),
        ("Jogurt naturalny", "2", "7,98"),
        ("Makaron", "1", "5,49"),
        ("Pomidory", "0,8 kg", "8,72"),
        ("Kawa", "1", "21,99"),
    ]
    x1, x2, x3 = 810, 1080, 1190
    text(d, (x1, 406), "Produkt", 15, "#64748b", True)
    text(d, (x2, 406), "Ilość", 15, "#64748b", True)
    text(d, (x3, 406), "Cena", 15, "#64748b", True)
    for i, row in enumerate(rows):
        y = 442 + i * 48
        d.line((810, y - 8, 1244, y - 8), fill="#e2e8f0", width=1)
        text(d, (x1, y), row[0], 16, "#111827")
        text(d, (x2, y), row[1], 16, "#111827")
        text(d, (x3, y), row[2], 16, "#111827")

    rounded(d, (1056, 638, 1244, 690), 14, "#16a34a")
    text(d, (1150, 652), "Zapisz wynik", 18, "#ffffff", True, "ma")

    img.save(OUT_DIR / "rys-03-edycja-placeholder.png", quality=95)


def github_placeholder():
    img, d = base(
        "Rys. 4. Praca zespołowa na GitHubie", "Miejsce na docelowy zrzut ekranu repozytorium lub GitHub Actions"
    )

    rounded(d, (90, 230, 1260, 704), 18, "#0f172a", "#334155", 2)
    text(d, (130, 266), "MattyMroz / SpendScan", 28, "#ffffff", True)
    text(d, (130, 306), "Pull requests, review i automatyczna kontrola jakości kodu", 18, "#94a3b8")

    tabs = ["Code", "Issues", "Pull requests", "Actions", "Projects"]
    for i, tab in enumerate(tabs):
        x = 130 + i * 170
        color = "#2563eb" if tab == "Actions" else "#1e293b"
        rounded(d, (x, 352, x + 142, 394), 10, color, "#334155", 1)
        text(d, (x + 18, 363), tab, 16, "#ffffff")

    jobs = [
        ("ruff", "passed", "#22c55e"),
        ("format", "passed", "#22c55e"),
        ("mypy", "passed", "#22c55e"),
        ("pytest", "passed", "#22c55e"),
    ]
    for i, (name, status, color) in enumerate(jobs):
        y = 430 + i * 58
        rounded(d, (130, y, 1220, y + 42), 12, "#111827", "#334155", 1)
        d.ellipse((154, y + 12, 174, y + 32), fill=color)
        text(d, (196, y + 10), name, 17, "#ffffff", True)
        text(d, (1070, y + 10), status, 17, "#86efac")

    rounded(d, (130, 636, 464, 680), 12, "#1d4ed8")
    text(d, (296, 648), "CI: automatyczna weryfikacja zmian", 16, "#ffffff", True, "ma")

    img.save(OUT_DIR / "rys-04-github-placeholder.png", quality=95)


if __name__ == "__main__":
    scan_placeholder()
    edit_placeholder()
    github_placeholder()
    print(f"Zapisano placeholdery w: {OUT_DIR}")  # noqa: T201
