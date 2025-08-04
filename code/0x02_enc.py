import re
import struct
import zlib
import hashlib
import cbor2

# Shortened keys for metadata
META_KEYS = {
    "Event": "E", "Site": "S", "Date": "D", "Round": "R",
    "White": "W", "Black": "B", "Result": "Rs",
    "WhiteElo": "WE", "BlackElo": "BE", "ECO": "EC",
}

def shorten_metadata(meta: dict) -> dict:
    """Shorten PGN metadata keys using META_KEYS mapping."""
    return {META_KEYS.get(k, k): v for k, v in meta.items()}

def split_pgn_games(content: str) -> list[str]:
    """Split PGN content into individual games."""
    games, current = [], []
    for line in content.splitlines():
        if line.strip().startswith('[Event '):
            if current:
                games.append('\n'.join(current).strip())
                current = []
        current.append(line)
    if current:
        games.append('\n'.join(current).strip())
    return games

def parse_single_game(game_text: str) -> tuple[dict, str]:
    """Extract metadata and move text from a single PGN game."""
    lines = game_text.strip().splitlines()
    metadata, moves_raw, in_moves = {}, [], False

    for line in lines:
        line = line.strip()
        if not line:
            in_moves = True
            continue
        if not in_moves and line.startswith('['):
            match = re.match(r'\[(\w+)\s+"(.*)"\]', line)
            if match:
                key, value = match.groups()
                metadata[key] = value
        else:
            in_moves = True
            moves_raw.append(line)

    move_text = ' '.join(moves_raw).strip()

    result_match = re.search(r'(1-0|0-1|1/2-1/2|\*)', move_text)
    if result_match:
        metadata["Result"] = result_match.group(1)

    return shorten_metadata(metadata), move_text

def encode_lossless(pgn_path: str, output_path: str, debug: bool = False):
    """Encode PGN file to binary .fbpgn format with deduplication."""
    with open(pgn_path, 'r', encoding='utf-8') as f:
        content = f.read()

    games = split_pgn_games(content)
    print(f"📊 Total games: {len(games)}")

    unique_map = {}
    encoded_chunks = []
    references = []

    for idx, game in enumerate(games):
        meta, move_text = parse_single_game(game)
        data = cbor2.dumps({'m': meta, 'mv': move_text})
        hash_ = hashlib.sha256(data).hexdigest()

        if hash_ not in unique_map:
            comp = data if debug else zlib.compress(data, level=9)
            unique_map[hash_] = len(encoded_chunks)
            encoded_chunks.append(comp)
            references.append(len(encoded_chunks) - 1)
            print(f"✅ Game {idx+1} | Unique | Len: {len(comp)}")
        else:
            references.append(unique_map[hash_])
            print(f"🔁 Game {idx+1} | Duplicate of #{unique_map[hash_]+1}")

    with open(output_path, 'wb') as f:
        f.write(b'FBPGN')                             # Magic header
        f.write(struct.pack('B', 0x02))               # Version
        f.write(struct.pack('<I', len(encoded_chunks)))
        for chunk in encoded_chunks:
            f.write(struct.pack('<I', len(chunk)))
            f.write(chunk)
        f.write(struct.pack('<I', len(references)))
        for ref in references:
            f.write(struct.pack('<I', ref))

    print(f"\n🎉 Finished → {output_path}")
    print(f"🧠 Unique games: {len(encoded_chunks)} | Total games: {len(references)}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python fbpgn_encoder.py input.pgn output.fbpgn")
    else:
        encode_lossless(sys.argv[1], sys.argv[2])
