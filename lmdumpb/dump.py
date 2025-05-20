#!/usr/bin/env python3
import argparse
import json
import lmdb
import os
from typing import Iterator, Any, IO, Dict

def parse_args() -> argparse.Namespace:
    """Parses command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Extract data from LMDB database and save in the specified format"
    )
    parser.add_argument(
        "-d", "--db", required=True, help="Path to the LMDB database"
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output file path (default: ./<dbname>-dump.<format_extension>)",
    )
    parser.add_argument(
        "-f",
        "--format",
        choices=["json", "html", "markdown"],
        default="json",
        help="Output format (default: json)",
    )
    return parser.parse_args()

def determine_output_file_path(
    db_path_str: str, output_arg: str | None, output_format_str: str
) -> str:
    """Determines the output file path based on arguments."""
    if output_arg:
        return output_arg

    db_name = os.path.basename(db_path_str)
    if "." in db_name:
        db_name = db_name.rsplit(".", 1)[0]

    format_extension = output_format_str
    if output_format_str == "markdown":
        format_extension = "md"
    return f"./{db_name}-dump.{format_extension}"

def ensure_output_directory_exists(output_file_path: str) -> None:
    """Ensures the directory for the output file exists."""
    output_dir = os.path.dirname(os.path.abspath(output_file_path))
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

def generate_lmdb_records(
    env: lmdb.Environment, error_accumulator: Dict[str, int]
) -> Iterator[Any]:
    """
    Generates records from the LMDB database.
    Tries to open a specific 'threads' database, falls back to the default database.
    Handles deserialization errors and updates the error_accumulator.
    """
    with env.begin(write=False) as txn:
        try:
            db = env.open_db(b"threads", txn=txn)
            cursor = txn.cursor(db=db)
            print("INFO: Using 'threads' database.")
        except lmdb.Error as e_db_open:
            print(
                f"INFO: Could not open database 'threads': {e_db_open}. Using default database."
            )
            cursor = txn.cursor()

        if not cursor.first():
            print("INFO: Database is empty.")
            return

        item_index = 0
        while True:
            item_index += 1
            try:
                key_bytes, value_bytes = cursor.item()
                try:
                    thread_data = json.loads(value_bytes.decode("utf-8"))
                    yield thread_data
                except (UnicodeDecodeError, json.JSONDecodeError) as e_deserialize:
                    key_str = key_bytes.decode("utf-8", "ignore")
                    print(
                        f"WARNING: Could not deserialize data for item (key: '{key_str}', internal index: {item_index}): {e_deserialize}"
                    )
                    error_accumulator["count"] += 1
            except lmdb.Error as e_item:
                print(
                    f"WARNING: Error retrieving item {item_index} from LMDB: {e_item}"
                )
                error_accumulator["count"] += 1
                # Attempt to advance cursor to avoid infinite loop on a problematic item
                # If cursor.next() fails here, the outer loop's condition will handle it.

            if not cursor.next():
                break

def serialize_to_json(
    records_iterator: Iterator[Any], file_handle: IO[str]
) -> int:
    """Serializes records to JSON format and writes to the file handle."""
    written_count = 0
    file_handle.write("[\n")
    first_item = True
    for record in records_iterator:
        if not first_item:
            file_handle.write(",\n")

        try:
            json_str = json.dumps(record, ensure_ascii=False, indent=2)
            file_handle.write(json_str)
            written_count += 1
        except TypeError as e_dump:
            print(f"WARNING: Could not serialize record to JSON: {e_dump}")
        first_item = False

    if first_item: # Handle case where iterator was empty
        file_handle.seek(0) # Go to start of file
        file_handle.write("[]") # Write empty JSON array
        file_handle.truncate() # Remove any trailing characters like "[\n"
    else:
        file_handle.write("\n]")
    return written_count

# --- HTML Serialization ---
def _html_escape(text: Any) -> str:
    """Basic HTML escaping for strings."""
    if not isinstance(text, str):
        text = str(text)
    import html
    return html.escape(text)

def _format_segment_html(segment: Dict[str, Any]) -> str:
    content = f"<h5>Segment (Type: {_html_escape(segment.get('type', 'N/A'))})</h5>"
    text_content = segment.get('text') or segment.get('content')
    if text_content:
        content += f"<p>{_html_escape(text_content)}</p>"
    if segment.get('diff'):
        content += f"<h6>Diff:</h6><pre>{_html_escape(segment.get('diff'))}</pre>"
    # Add other relevant segment fields if necessary
    return content

def _format_tool_interaction_html(interaction: Dict[str, Any], interaction_type: str) -> str:
    interaction_id = interaction.get('id') or interaction.get('tool_use_id')
    name = interaction.get('name', 'N/A')

    content = f"<h5>{interaction_type}: {_html_escape(name)} (ID: {_html_escape(interaction_id)})</h5>"

    data_to_display = None
    if 'input' in interaction:
        content += "<h6>Input:</h6>"
        data_to_display = interaction['input']
    elif 'output' in interaction and interaction['output'] is not None:
        content += "<h6>Output:</h6>"
        data_to_display = interaction['output']
    elif 'content' in interaction and interaction_type == "Tool Result": # For tool result content
        content += "<h6>Content:</h6>"
        data_to_display = interaction['content']

    if isinstance(data_to_display, (dict, list)):
        try:
            content += f"<pre>{_html_escape(json.dumps(data_to_display, indent=2))}</pre>"
        except TypeError:
            content += f"<pre>{_html_escape(str(data_to_display))}</pre>"
    elif data_to_display is not None:
        content += f"<p>{_html_escape(data_to_display)}</p>"

    if interaction.get('is_error', False):
        content += "<p><strong>Error: True</strong></p>"
    return content

def _format_message_html(message: Dict[str, Any]) -> str:
    msg_id = message.get('id', 'N/A')
    role = message.get('role', 'N/A')
    content = f"<section class='message'><h4>Message ID: {_html_escape(msg_id)} (Role: {_html_escape(role)})</h4>"

    segments = message.get('segments', [])
    if segments:
        content += "<div class='segments'>"
        for seg in segments:
            content += _format_segment_html(seg)
        content += "</div>"

    tool_uses = message.get('tool_uses', [])
    if tool_uses:
        content += "<div class='tool-uses'>"
        for tu in tool_uses:
            content += _format_tool_interaction_html(tu, "Tool Use")
        content += "</div>"

    tool_results = message.get('tool_results', [])
    if tool_results:
        content += "<div class='tool-results'>"
        for tr in tool_results:
            content += _format_tool_interaction_html(tr, "Tool Result")
        content += "</div>"
    content += "</section>"
    return content

def serialize_to_html(
    records_iterator: Iterator[Any], file_handle: IO[str], db_path_str: str
) -> int:
    """Serializes records to structured HTML format."""
    written_count = 0
    file_handle.write(f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LMDB Dump - {os.path.basename(db_path_str)}</title>
    <style>
        body {{ font-family: sans-serif; margin: 20px; line-height: 1.6; }}
        article.record {{ border: 1px solid #ccc; padding: 15px; margin-bottom: 20px; border-radius: 5px; }}
        section.message {{ margin-top: 15px; padding-left: 15px; border-left: 3px solid #eee; }}
        h1, h2, h3, h4, h5 {{ margin-top: 0.5em; margin-bottom: 0.25em; }}
        pre {{ background-color: #f4f4f4; padding: 10px; border-radius: 3px; white-space: pre-wrap; word-wrap: break-word; }}
        .segments, .tool-uses, .tool-results {{ margin-left: 20px; }}
    </style>
</head>
<body>
    <h1>LMDB Dump: {os.path.basename(db_path_str)}</h1>
""")

    for record_idx, record in enumerate(records_iterator):
        file_handle.write(f"<article class='record'><h2>Record {record_idx + 1}</h2>")
        if record.get('summary'):
            file_handle.write(f"<h3>Summary: {_html_escape(record.get('summary'))}</h3>")
        file_handle.write(f"<p><strong>Version:</strong> {_html_escape(record.get('version', 'N/A'))}</p>")
        file_handle.write(f"<p><strong>Updated At:</strong> {_html_escape(record.get('updated_at', 'N/A'))}</p>")

        messages = record.get('messages', [])
        for msg in messages:
            file_handle.write(_format_message_html(msg))

        file_handle.write("</article>")
        written_count += 1

    if written_count == 0:
        file_handle.write("<p>No records found or processed.</p>")

    file_handle.write("\n</body>\n</html>\n")
    return written_count

# --- Markdown Serialization ---
def _md_escape(text: Any) -> str:
    """Basic Markdown escaping for strings (primarily for code blocks)."""
    if not isinstance(text, str):
        text = str(text)
    # For general markdown, more escaping might be needed, but for JSON in code blocks, this is minimal.
    return text.replace('`', '\\`')


def _format_segment_md(segment: Dict[str, Any]) -> str:
    content = f"##### Segment (Type: `{_md_escape(segment.get('type', 'N/A'))}`)\n"
    text_content = segment.get('text') or segment.get('content')
    if text_content:
        content += f"\n{_md_escape(text_content)}\n\n"
    if segment.get('diff'):
        content += f"###### Diff:\n```\n{_md_escape(segment.get('diff'))}\n```\n\n"
    return content

def _format_tool_interaction_md(interaction: Dict[str, Any], interaction_type: str) -> str:
    interaction_id = interaction.get('id') or interaction.get('tool_use_id')
    name = interaction.get('name', 'N/A')

    content = f"##### {interaction_type}: `{_md_escape(name)}` (ID: `{_md_escape(interaction_id)}`)\n"

    data_to_display = None
    data_label = ""
    if 'input' in interaction:
        data_label = "Input"
        data_to_display = interaction['input']
    elif 'output' in interaction and interaction['output'] is not None:
        data_label = "Output"
        data_to_display = interaction['output']
    elif 'content' in interaction and interaction_type == "Tool Result":
        data_label = "Content"
        data_to_display = interaction['content']

    if data_to_display is not None:
        content += f"###### {data_label}:\n"
        if isinstance(data_to_display, (dict, list)):
            try:
                content += f"```json\n{json.dumps(data_to_display, indent=2)}\n```\n\n"
            except TypeError:
                content += f"```\n{_md_escape(str(data_to_display))}\n```\n\n"
        else:
            content += f"{_md_escape(data_to_display)}\n\n"

    if interaction.get('is_error', False):
        content += "**Error: True**\n\n"
    return content

def _format_message_md(message: Dict[str, Any]) -> str:
    msg_id = message.get('id', 'N/A')
    role = message.get('role', 'N/A')
    content = f"#### Message ID: `{_md_escape(msg_id)}` (Role: `{_md_escape(role)}`)\n"

    segments = message.get('segments', [])
    if segments:
        content += "\n###### Segments:\n"
        for seg in segments:
            content += _format_segment_md(seg)

    tool_uses = message.get('tool_uses', [])
    if tool_uses:
        content += "\n###### Tool Uses:\n"
        for tu in tool_uses:
            content += _format_tool_interaction_md(tu, "Tool Use")

    tool_results = message.get('tool_results', [])
    if tool_results:
        content += "\n###### Tool Results:\n"
        for tr in tool_results:
            content += _format_tool_interaction_md(tr, "Tool Result")
    return content + "\n---\n"


def serialize_to_markdown(
    records_iterator: Iterator[Any], file_handle: IO[str], db_path_str: str
) -> int:
    """Serializes records to structured Markdown format."""
    written_count = 0
    file_handle.write(f"# LMDB Dump: {os.path.basename(db_path_str)}\n\n")

    for record_idx, record in enumerate(records_iterator):
        file_handle.write(f"## Record {record_idx + 1}\n\n")
        if record.get('summary'):
            file_handle.write(f"**Summary:** {_md_escape(record.get('summary'))}\n\n")
        file_handle.write(f"- **Version:** `{_md_escape(record.get('version', 'N/A'))}`\n")
        file_handle.write(f"- **Updated At:** `{_md_escape(record.get('updated_at', 'N/A'))}`\n\n")

        messages = record.get('messages', [])
        if messages:
            file_handle.write("### Messages\n\n")
            for msg in messages:
                file_handle.write(_format_message_md(msg))

        written_count += 1
        file_handle.write("\n***\n\n") # Separator for records

    if written_count == 0:
        file_handle.write("No records found or processed.\n")

    return written_count

def print_summary(
    written_items_count: int, deserialization_error_count: int, output_file_path: str
) -> None:
    """Prints the summary of the extraction process."""
    print(
        f"Data extraction complete. Successfully wrote {written_items_count} items."
    )
    if deserialization_error_count > 0:
        print(
            f"Encountered {deserialization_error_count} errors during data deserialization."
        )
    print(f"Data saved to {output_file_path}")

def main():
    """Main function to orchestrate LMDB data extraction."""
    args = parse_args()

    output_file = determine_output_file_path(args.db, args.output, args.format)
    ensure_output_directory_exists(output_file)

    deserialization_errors = {"count": 0}
    written_count = 0

    env: lmdb.Environment | None = None
    try:
        env = lmdb.open(args.db, readonly=True, max_dbs=5) # Increased max_dbs just in case, 1 is often fine.

        if env is not None:  # Ensure env is not None before passing to generate_lmdb_records
            records_iter = generate_lmdb_records(env, deserialization_errors)

            with open(output_file, "w", encoding="utf-8") as f:
                if args.format == "json":
                    written_count = serialize_to_json(records_iter, f)
                elif args.format == "html":
                    written_count = serialize_to_html(records_iter, f, args.db)
                elif args.format == "markdown":
                    written_count = serialize_to_markdown(records_iter, f, args.db)
                else:
                    # This case should ideally not be reached due to argparse choices
                    print(f"ERROR: Unknown format '{args.format}'")
                    # No specific return here, summary will indicate 0 items written if error occurs before serialization.
        else:
            print("ERROR: Failed to open LMDB environment")

    except lmdb.Error as e_lmdb:
        print(f"LMDB ERROR: {e_lmdb}")
        # written_count remains 0, deserialization_errors might be partial
    except IOError as e_io:
        print(f"FILE I/O ERROR writing to {output_file}: {e_io}")
    except Exception as e_unexpected:
        print(f"An UNEXPECTED ERROR occurred: {e_unexpected}")
    finally:
        if env:
            env.close()

    print_summary(written_count, deserialization_errors["count"], output_file)

if __name__ == "__main__":
    main()
