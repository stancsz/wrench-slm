"""Render the Wrench SLM plus LLM gateway architecture as a PNG."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


OUT = Path(__file__).resolve().parents[1] / "docs" / "architecture" / "wrench-slm-llm-gateway.png"
W, H = 2400, 1420
BG, INK, MUTED, LINE = "#F7F9FC", "#152033", "#526176", "#93A4BA"
BLUE, BLUE_DARK = "#DCEBFF", "#2563EB"
GREEN, GREEN_DARK = "#DCFCE7", "#15803D"
AMBER, AMBER_DARK = "#FEF3C7", "#B45309"
PURPLE, PURPLE_DARK = "#F3E8FF", "#7E22CE"
RED, RED_DARK = "#FEE2E2", "#B91C1C"
GRAY = "#E9EEF5"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    face = "arialbd.ttf" if bold else "arial.ttf"
    return ImageFont.truetype(face, size)


def center_text(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], text: str, size: int = 28, fill: str = INK, bold: bool = False) -> None:
    f = font(size, bold)
    lines = text.split("\n")
    heights = [draw.textbbox((0, 0), line, font=f)[3] for line in lines]
    y = box[1] + (box[3] - box[1] - sum(heights) - (len(lines) - 1) * 8) / 2
    for line, height in zip(lines, heights):
        width = draw.textbbox((0, 0), line, font=f)[2]
        draw.text(((box[0] + box[2] - width) / 2, y), line, font=f, fill=fill)
        y += height + 8


def box(draw: ImageDraw.ImageDraw, xy: tuple[int, int, int, int], title: str, detail: str, fill: str, accent: str) -> None:
    draw.rounded_rectangle(xy, radius=24, fill=fill, outline=accent, width=3)
    draw.rounded_rectangle((xy[0], xy[1], xy[0] + 13, xy[3]), radius=8, fill=accent)
    center_text(draw, (xy[0] + 24, xy[1] + 18, xy[2] - 12, xy[1] + 72), title, 30, INK, True)
    center_text(draw, (xy[0] + 25, xy[1] + 75, xy[2] - 12, xy[3] - 16), detail, 22, MUTED)


def arrow(draw: ImageDraw.ImageDraw, start: tuple[int, int], end: tuple[int, int], label: str = "", color: str = LINE, dashed: bool = False) -> None:
    if dashed:
        steps = 16
        for i in range(0, steps, 2):
            a, b = i / steps, (i + 1) / steps
            draw.line((start[0] + (end[0] - start[0]) * a, start[1] + (end[1] - start[1]) * a, start[0] + (end[0] - start[0]) * b, start[1] + (end[1] - start[1]) * b), fill=color, width=4)
    else:
        draw.line((*start, *end), fill=color, width=5)
    draw.polygon([(end[0], end[1]), (end[0] - 18, end[1] - 10), (end[0] - 18, end[1] + 10)], fill=color)
    if label:
        f = font(20, True)
        mid = ((start[0] + end[0]) / 2, (start[1] + end[1]) / 2)
        draw.rounded_rectangle((mid[0] - 115, mid[1] - 22, mid[0] + 115, mid[1] + 22), radius=9, fill=BG)
        width = draw.textbbox((0, 0), label, font=f)[2]
        draw.text((mid[0] - width / 2, mid[1] - 13), label, font=f, fill=color)


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(image)

    draw.text((90, 55), "Wrench gateway: safe SLM + LLM collaboration", font=font(48, True), fill=INK)
    draw.text((92, 120), "The local SLM can propose only bounded developer-tool actions. The gateway preserves the original request and escalates every miss.", font=font(24), fill=MUTED)

    # Horizontal workflow
    box(draw, (90, 280, 345, 450), "Client", "Developer tool\nor application", GRAY, "#64748B")
    box(draw, (440, 280, 770, 450), "Gateway policy", "Eligibility gate\nRules own rigid work", BLUE, BLUE_DARK)
    box(draw, (865, 190, 1225, 365), "Local Wrench SLM", "One bounded proposal\nQwen-derived sparse model", GREEN, GREEN_DARK)
    box(draw, (865, 480, 1225, 655), "LLM fallback", "Strong-model path\nfor non-eligible or failed work", PURPLE, PURPLE_DARK)
    box(draw, (1320, 190, 1700, 365), "Independent verifier", "Schema, paths, bounds,\npermissions, task-family rules", AMBER, AMBER_DARK)
    box(draw, (1795, 190, 2135, 365), "Bounded executor", "Read-only allowed actions\nNever generic shell or writes", GREEN, GREEN_DARK)
    box(draw, (1795, 480, 2135, 655), "Final response", "Observation returned\nto the calling client", BLUE, BLUE_DARK)

    arrow(draw, (345, 365), (440, 365))
    arrow(draw, (770, 315), (865, 275), "eligible", GREEN_DARK)
    arrow(draw, (770, 415), (865, 565), "otherwise", PURPLE_DARK)
    arrow(draw, (1225, 275), (1320, 275), "strict JSON", GREEN_DARK)
    arrow(draw, (1700, 275), (1795, 275), "accepted", GREEN_DARK)
    arrow(draw, (1965, 365), (1965, 480), "observation", GREEN_DARK)
    arrow(draw, (1225, 565), (1795, 565), "original request", PURPLE_DARK)
    # Verifier rejection turns down to fallback.
    draw.line((1510, 365, 1510, 565), fill=RED_DARK, width=5)
    draw.line((1510, 565, 1795, 565), fill=RED_DARK, width=5)
    draw.polygon([(1795, 565), (1777, 555), (1777, 575)], fill=RED_DARK)
    draw.text((1532, 420), "malformed, unsafe, timeout, abstain", font=font(20, True), fill=RED_DARK)
    draw.text((1532, 450), "or circuit open", font=font(20, True), fill=RED_DARK)

    # Control plane
    draw.rounded_rectangle((90, 820, 2135, 1160), radius=28, fill="#EEF3F9", outline="#93A4BA", width=2)
    draw.text((130, 855), "Control plane that keeps collaboration safe", font=font(32, True), fill=INK)
    box(draw, (135, 940, 570, 1105), "ProposalRouter", "Finite attempts\nCancellation, bypass, circuit breaker", BLUE, BLUE_DARK)
    box(draw, (720, 940, 1155, 1105), "State persistence", "Schema and configuration\nhash-bound restore", GRAY, "#64748B")
    box(draw, (1305, 940, 1740, 1105), "Trace and metrics", "Events, decisions, usage,\noutcome receipts", GRAY, "#64748B")
    box(draw, (1890, 940, 2090, 1105), "Rollout gate", "Learned routing\nDISABLED", RED, RED_DARK)
    arrow(draw, (570, 1022), (720, 1022), color=BLUE_DARK, dashed=True)
    arrow(draw, (1155, 1022), (1305, 1022), color=BLUE_DARK, dashed=True)
    arrow(draw, (1740, 1022), (1890, 1022), color=BLUE_DARK, dashed=True)
    arrow(draw, (1045, 365), (1045, 940), color=BLUE_DARK, dashed=True)
    arrow(draw, (1510, 365), (1510, 940), color=AMBER_DARK, dashed=True)

    draw.text((90, 1240), "Current implementation", font=font(28, True), fill=INK)
    draw.text((390, 1240), "Local adapter -> strict parser -> verifier -> read-only executor", font=font(26), fill=GREEN_DARK)
    draw.text((90, 1300), "Planned integration boundary", font=font(28, True), fill=INK)
    draw.text((455, 1300), "An LLM provider connector belongs only behind the fallback handoff, never inside the executor authority boundary.", font=font(26), fill=PURPLE_DARK)
    image.save(OUT)
    print(OUT)


if __name__ == "__main__":
    main()
