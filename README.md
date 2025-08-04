FBPGN SPECIFICATION (v0x02)
===========================

Format Name: FBPgn (Full Binary PGN)
Version: 0x02
Author: Yoga Ardiansyah
Last Updated: 2025-08-04

----------------------------------------
OVERVIEW
----------------------------------------

FBPgn (.fbpgn) is a binary container format for efficiently storing chess games, intended to replace PGN or CSV for machine learning and large-scale analysis.

- Compresses and deduplicates games
- Stores structured metadata and move text in CBOR
- Suitable for direct loading into ML pipelines
- Portable, fast, and optimized for scale

----------------------------------------
FILE STRUCTURE
----------------------------------------

All integers are little-endian (unsigned).

[HEADER]
- 5 bytes  : Magic header ("FBPGN")
- 1 byte   : Version (0x02)
- 4 bytes  : Number of unique game chunks (N_chunks)

[CHUNKS]
For each of N_chunks:
- 4 bytes  : Length of compressed chunk (L)
- L bytes  : Zlib-compressed CBOR data

[REFERENCES]
- 4 bytes  : Number of references (N_refs)
- N_refs x 4 bytes : uint32 index into chunk array

Total number of games = N_refs  
Total number of unique games = N_chunks

----------------------------------------
CBOR CHUNK SCHEMA
----------------------------------------

Each chunk (after decompression) is a CBOR map of the following structure:

{
  "m": {meta},
  "mv": "<move text>"
}

Where:

- "m" = metadata dictionary with compressed keys (see below)
- "mv" = move sequence string (PGN style, e.g. "1. e4 e5 2. Nf3 Nc6")

Example:

{
  "m": {"W": "Carlsen", "B": "Nepo", "Rs": "1-0", "WE": "2849", "BE": "2789", "EC": "B90"},
  "mv": "1. e4 c5 2. Nf3 d6 3. d4 cxd4 ..."
}

----------------------------------------
METADATA KEYS (SHORTENED)
----------------------------------------

The following keys from PGN are shortened for storage:

| PGN Key   | Short Key |
|----------|-----------|
| Event    | E         |
| Site     | S         |
| Date     | D         |
| Round    | R         |
| White    | W         |
| Black    | B         |
| Result   | Rs        |
| WhiteElo | WE        |
| BlackElo | BE        |
| ECO      | EC        |

Other keys may be stored as-is if not in this table.

----------------------------------------
OPTIONAL: .fbpgn.idx INDEX FILE
----------------------------------------

Separate index file in JSON format, enabling metadata queries without decompressing all chunks.

Example (.fbpgn.idx):

[
  {"ref": 0, "W": "Carlsen", "B": "Nepo", "Rs": "1-0", "EC": "B90"},
  {"ref": 1, "W": "Firouzja", "B": "Giri", "Rs": "0-1", "EC": "C42"}
]

Use case:
- Filter games by player, result, ECO without parsing .fbpgn
- Faster tooling & UI support

----------------------------------------
VERSION HISTORY
----------------------------------------

v0x01 - Initial version
v0x02 - Adds:
  - Indexing support via .idx
  - CBOR payload standardization
  - Full metadata key table
  - Deduplication via hash references

----------------------------------------
PLANNED EXTENSIONS
----------------------------------------

Future features may include:

- "tok": [int] → Tokenized moves for ML use
- "features": {"elo": int, ...} → Preprocessed numerical fields
- Game-level SHA256 checksum
- Chunk offset table (for memory-mapped seeking)
- Flag for compressed/uncompressed chunks
- Game tagging / annotation support

----------------------------------------
CONTACT / LICENSE
----------------------------------------

This format is open and extensible.
Feel free to implement compatible tools in any language.

© 2025 Yoga Ardiansyah
License: MIT / Public Domain
