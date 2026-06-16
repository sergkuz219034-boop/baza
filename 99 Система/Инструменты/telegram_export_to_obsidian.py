from __future__ import annotations

import argparse
import html
import re
from datetime import datetime
from pathlib import Path


MONTHS = {
    "January": "01",
    "February": "02",
    "March": "03",
    "April": "04",
    "May": "05",
    "June": "06",
    "July": "07",
    "August": "08",
    "September": "09",
    "October": "10",
    "November": "11",
    "December": "12",
}


def sanitize_filename(value: str) -> str:
    value = re.sub(r'[<>:"/\\\\|?*]+', "_", value)
    value = re.sub(r"\s+", " ", value).strip(" ._")
    return value or "Без_названия"


def parse_export_date(value: str) -> str | None:
    value = value.strip()
    m = re.match(r"(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})", value)
    if not m:
        return None
    day, month_name, year = m.groups()
    month = MONTHS.get(month_name)
    if not month:
        return None
    return f"{year}-{month}-{int(day):02d}"


def parse_message_date(value: str) -> tuple[str | None, str | None]:
    value = value.strip()
    m = re.match(r"(\d{2})\.(\d{2})\.(\d{4})\s+(\d{2}:\d{2})", value)
    if not m:
        return None, None
    day, month, year, time = m.groups()
    return f"{year}-{month}-{day}", time


def russian_date(iso_date: str | None) -> str:
    if not iso_date:
        return ""
    try:
        return datetime.strptime(iso_date, "%Y-%m-%d").strftime("%d.%m.%Y")
    except ValueError:
        return iso_date


def extract_between(pattern: str, text: str, flags: int = re.S) -> str | None:
    m = re.search(pattern, text, flags)
    return m.group(1) if m else None


def clean_fragment(fragment: str | None) -> str:
    if not fragment:
        return ""
    fragment = fragment.replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")
    fragment = re.sub(r"</p\s*>", "\n", fragment, flags=re.I)
    fragment = re.sub(r"</div\s*>", "\n", fragment, flags=re.I)
    fragment = re.sub(r"<li[^>]*>", "- ", fragment, flags=re.I)
    fragment = re.sub(r"</li\s*>", "\n", fragment, flags=re.I)
    fragment = re.sub(r"<[^>]+>", "", fragment)
    fragment = html.unescape(fragment)
    fragment = re.sub(r"\n{3,}", "\n\n", fragment)
    fragment = re.sub(r"[ \t]+\n", "\n", fragment)
    return fragment.strip()


def split_message_blocks(html_text: str) -> list[str]:
    starts = [m.start() for m in re.finditer(r'<div class="message ', html_text)]
    blocks: list[str] = []
    for index, start in enumerate(starts):
        end = starts[index + 1] if index + 1 < len(starts) else len(html_text)
        blocks.append(html_text[start:end])
    return blocks


def detect_media(block: str) -> str | None:
    patterns = [
        (r'class="[^"]*\bphoto\b[^"]*"', "Фото"),
        (r'class="[^"]*\bsticker\b[^"]*"', "Стикер"),
        (r'class="[^"]*\bvideo\b[^"]*"', "Видео"),
        (r'class="[^"]*\bvoice\b[^"]*"', "Голосовое"),
        (r'class="[^"]*\bfile\b[^"]*"', "Файл"),
        (r'class="[^"]*\blocation\b[^"]*"', "Локация"),
        (r'class="[^"]*\bcontact\b[^"]*"', "Контакт"),
        (r'class="[^"]*\bcall\b[^"]*"', "Звонок"),
    ]
    for pattern, label in patterns:
        if re.search(pattern, block):
            return label
    return None


def parse_chat_file(messages_path: Path) -> dict:
    html_text = messages_path.read_text(encoding="utf-8", errors="ignore")
    header_region = html_text.split('<div class="page_body chat_page">', 1)[0]
    title = clean_fragment(extract_between(r'<div class="text bold">\s*(.*?)\s*</div>', header_region)) or messages_path.parent.name

    blocks = split_message_blocks(html_text)
    messages: list[dict] = []
    participants: list[str] = []
    date_from: str | None = None
    date_to: str | None = None
    last_speaker: str | None = None

    for block in blocks:
        cls = extract_between(r'<div class="message ([^"]+)"', block) or ""
        if "service" in cls:
            service = clean_fragment(extract_between(r'<div class="body details">\s*(.*?)\s*</div>', block))
            iso = parse_export_date(service)
            if iso:
                date_from = date_from or iso
                date_to = iso
            messages.append({"kind": "service", "service": service, "iso": iso})
            continue

        date_raw = extract_between(r'<div class="pull_right date details"[^>]*title="([^"]+)"', block) or ""
        iso_date, time = parse_message_date(date_raw)
        if iso_date:
            date_from = date_from or iso_date
            date_to = iso_date

        speaker = clean_fragment(extract_between(r'<div class="from_name">\s*(.*?)\s*</div>', block))
        if not speaker and "joined" in cls and last_speaker:
            speaker = last_speaker
        if speaker and speaker not in participants:
            participants.append(speaker)
        if speaker:
            last_speaker = speaker

        text = clean_fragment(extract_between(r'<div class="text(?: [^"]*)?">\s*(.*?)\s*</div>', block))
        if not text:
            media = detect_media(block)
            text = f"[{media}]" if media else ""

        messages.append(
            {
                "kind": "message",
                "speaker": speaker or "Без имени",
                "iso": iso_date,
                "time": time,
                "text": text,
                "media": detect_media(block),
            }
        )

    return {
        "title": title,
        "messages": messages,
        "participants": participants,
        "date_from": date_from,
        "date_to": date_to,
        "source_file": messages_path,
    }


def render_note(data: dict, export_name: str, chat_id: str, source_root: Path) -> str:
    title = data["title"]
    messages = data["messages"]
    participants = data["participants"]
    date_from = data["date_from"]
    date_to = data["date_to"]
    source_file = data["source_file"]

    note_lines = [
        "---",
        'type: "telegram-dialogue"',
        f'export: "{export_name}"',
        f'chat_id: "{chat_id}"',
        f'title: "{title}"',
        f'messages_count: {len(messages)}',
    ]
    if participants:
        note_lines.append("participants:")
        for participant in participants:
            note_lines.append(f'  - "{participant}"')
    if date_from:
        note_lines.append(f'date_from: "{date_from}"')
    if date_to:
        note_lines.append(f'date_to: "{date_to}"')
    note_lines.extend(
        [
            f'source_file: "{source_file.as_posix()}"',
            "---",
            f"# Диалог: {title}",
            "",
            f"> **Источник**: Telegram export `{export_name}`",
            f"> **Чат**: `{chat_id}`",
            f"> **Файл**: `{source_file.name}`",
        ]
    )
    if date_from or date_to:
        if date_from == date_to:
            note_lines.append(f"> **Период**: {russian_date(date_from)}")
        else:
            note_lines.append(
                f"> **Период**: {russian_date(date_from)} — {russian_date(date_to)}"
            )
    note_lines.append(f"> **Сообщений**: {len(messages)}")
    if participants:
        note_lines.append(f"> **Участники**: {', '.join(participants)}")

    note_lines.extend(
        [
            "",
            "## Автосводка",
            "- Это прямой перевод Telegram-экспорта в Markdown-формат для Obsidian.",
            "- Смысл диалога не интерпретируется автоматически, чтобы не терять факты.",
            "- Вложения помечаются только как тип, без копирования медиа.",
            "",
            "## Переписка",
        ]
    )

    current_day: str | None = None
    for message in messages:
        if message["kind"] == "service":
            if message["iso"] and message["iso"] != current_day:
                current_day = message["iso"]
                note_lines.extend(["", f"### {russian_date(current_day)}"])
            elif message["service"]:
                note_lines.extend(["", f"### {message['service']}"])
            continue

        if message["iso"] and message["iso"] != current_day:
            current_day = message["iso"]
            note_lines.extend(["", f"### {russian_date(current_day)}"])

        time = message["time"] or "--:--"
        speaker = message["speaker"]
        text = message["text"] or "[Сообщение без текста]"
        note_lines.append(f"- **{time}** {speaker}: {text}")

    note_lines.append("")
    return "\n".join(note_lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert Telegram HTML exports into Obsidian markdown notes.")
    parser.add_argument(
        "--source",
        action="append",
        required=True,
        help="Root folder that contains Telegram chat folders with messages.html",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Destination folder inside the Obsidian vault",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Process only the first N chats if set to a positive value",
    )
    args = parser.parse_args()

    output_root = Path(args.output)
    output_root.mkdir(parents=True, exist_ok=True)

    sources = [Path(item) for item in args.source]
    processed = 0
    for source_root in sources:
        if not source_root.exists():
            continue

        export_name = source_root.parent.name
        for messages_path in sorted(source_root.rglob("messages.html")):
            if args.limit and processed >= args.limit:
                return 0

            chat_dir = messages_path.parent
            chat_id = chat_dir.name
            data = parse_chat_file(messages_path)
            title = sanitize_filename(data["title"])
            note_name = f"{chat_id} - {title}.md"
            note_path = output_root / f"{export_name} - {note_name}"
            note_path.write_text(
                render_note(data, export_name, chat_id, source_root),
                encoding="utf-8",
            )
            processed += 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
