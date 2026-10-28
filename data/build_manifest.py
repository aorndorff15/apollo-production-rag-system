
import json
from pathlib import Path

# Find the project folder and its data folder
project_folder = Path(__file__).parent
data_folder = project_folder
manifest_path = data_folder / "manifest.json"

documents = []

# Look through the data folder and all its subfolders
for file_path in sorted(data_folder.rglob("*")):

    # Include PDF and HTML files
    if not file_path.is_file() or file_path.suffix.lower() not in [".pdf", ".html"]:
        continue

    # Work out which collection the file belongs to
    relative_path = file_path.relative_to(data_folder)
    folder_name = relative_path.parts[0]

    if folder_name == "mission_overviews":
        source_name = "NASA"
    elif folder_name == "transcripts":
        source_name = "NASA"
    elif folder_name == "press_kits":
        source_name = "NASA"
    elif folder_name == "html_documents":
        source_name = "Smithsonian National Air and Space Museum HTML Documents"
    elif folder_name == "distractors":
        source_name = "Mixed distractor sources"
    else:
        source_name = "Uncategorized"

    is_distractor = folder_name == "distractors"

    # Add the file's information to the manifest
    documents.append({
        "title": file_path.stem,
        "path": str(relative_path),
        "format": file_path.suffix.lower().lstrip("."),
        "source_name": source_name,
        "is_distractor": is_distractor,
        "relevance": "distractor" if is_distractor else "relevant",
        "token_count": None
    })


# Calculate the current corpus totals automatically
formats = {}
sources = {}

for doc in documents:
    file_format = doc["format"]
    source_name = doc["source_name"]

    formats[file_format] = formats.get(file_format, 0) + 1
    sources[source_name] = sources.get(source_name, 0) + 1

# Count the documents marked as distractors
distractor_count = sum(
    1 for doc in documents if doc["is_distractor"]
)

# Create the manifest with current totals and assignment requirements
manifest = {
    "project": "Apollo RAG Milestone 2",

    "current_corpus": {
        "total_files": len(documents),
        "formats": formats,
        "sources": sources,
        "total_tokens": None,
        "distractor_files": distractor_count
    },

    "requirements": {
        "minimum_documents": 50,
        "minimum_sources": 3,
        "minimum_file_formats": 2,
        "minimum_total_tokens": 250001,
        "target_distractor_percentage": 15
    },

    "documents": documents
}

# Save the manifest
with open(manifest_path, "w", encoding="utf-8") as file:
    json.dump(manifest, file, indent=2)

# Display the results
print(f"Manifest created: {manifest_path}")
print(f"Total files: {len(documents)}")

print("\nFiles by format:")
for file_format, count in sorted(formats.items()):
    print(f"  {file_format}: {count}")

print("\nFiles by source:")
for source_name, count in sorted(sources.items()):
    print(f"  {source_name}: {count}")

print(f"\nDistractor files: {distractor_count}")

