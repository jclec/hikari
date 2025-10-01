#!/usr/bin/env python
"""
Highlight connections between kanji compounds by shared component kanjis

Takes in either:
    1. a txt file containing words (default 'words.txt')
    2. a json file from jpdb's data export (default 'reviews.json')
    - for details, see read_from_jpdb()
and returns a JSON file containing two objects:

1. Component kanji -> all words containing it
- Non-kanji components (e.g. kana) are not used as keys
2. Words -> other words that share any kanji
- Partial-kanji words are included as keys
- Non-kanji characters (e.g. kana) are not considered

Fully non-kanji (kana, alphanumeric, etc.) words are ignored but partial-kanji words are still
processed to allow words like 楽しい

For example, inputting "今朝 今晩 朝食 食べる 楽しい かな english!" should return:
{
    "components": {
        "今": ["今朝", "今晩"],
        "朝": ["今晩", "朝食"],
        "晩": ["今晩"],
        "食": ["朝食", "食べる"],
        "楽": ["楽しい"]
    },
    "related_words": {
        "今朝": ["今晩", "朝食"],
        "今晩": ["今朝"],
        "朝食": ["今朝", "食べる"],
        "食べる": ["朝食"],
        "楽しい": []
    }
}
(note lack of "かな" and "english!")

Running with no arguments will take in 'words.txt' and output 'output.json'
"""

import sys
from collections import defaultdict
import re
import json
from typing import List, Dict, DefaultDict, Set, Iterable
import argparse

debug = False


def main(
    file_path: str, delimiter: str | None, from_jpdb: bool, save_path: str
) -> None:
    if delimiter and re.search(r"[一-龯ぁ-んァ-ン]", delimiter):
        print(f"delimiter（{delimiter}）cannot be a japanese character!")
        sys.exit(2)

    if from_jpdb:
        # named "words" instead of "(kanji) compounds" bc may contain non-kanji
        words: List[str] = read_from_jpdb(file_path)
    else:
        words: List[str] = read_from_txt(file_path, delimiter)
    # sort words for consistency
    words.sort()

    components: DefaultDict[str, List[str]] = separate_words(words)
    related_words: Dict[str, Set[str]] = relate_words(words, components)

    # normalize dicts to dict[str, list[str]] for jsonification
    # also sort lists for consistency
    components = {k: sorted(list(w)) for k, w in components.items()}
    related_words = {w: sorted(list(rw)) for w, rw in related_words.items()}

    save_to_json(save_path, components, related_words)


def read_from_txt(txt_file: str, delimiter: str | None) -> List[str]:
    """
    Reads txt file containing words and splits them into list of words

    By default the words are split using the default split() delimiter (any whitespace), but it can
    also be specified using the delimiter param

    All-kana (no kanji) words are ignored

    Arguments:
    - file (path): str
    - delimiter: str | None

    Returns:
    List[str] - list of all words
    """
    with open(txt_file, "r", encoding="utf-8") as f:
        text = f.read()
    words = text.split(delimiter)
    # remove fully non-kanji and empty words
    words = [w for w in words if has_kanji(w)]

    if debug:
        print(words[:5], "\n")
    return words


def read_from_jpdb(json_file: str) -> List[str]:
    """
    Reads json file from jpdb review export and returns a list of words
    All-kana (no kanji) words are ignored


    jpdb export json schema:
    {
        "cards_vocabulary_jp_en": [
            {
                "vid": int (vocab id),
                "spelling": str (kanji/hiragana),
                "reading": str (hiragana only),
                "reviews": [
                    { "timestamp": int, "grade": str, "from_anki": bool },
                    ...
                ]
            },
            ...
        ],
        "cards_vocabulary_en_jp": [ (omitted) ],
        "cards_kanji_keyword_char": [ (omitted) ],
        "cards_kanji_char_keyword": [ (omitted) ]
    }

    Arguments:
    - file (path): str

    Returns:
    List[str] - list of all words
    """
    with open(json_file, "r", encoding="utf-8") as f:
        data: dict = json.load(f)

    # get jp -> en cards
    cards = data.get("cards_vocabulary_jp_en")
    if cards is None:
        print("key 'cards_vocabulary_jp_en' not found")
        sys.exit(data.keys())

    # get kanji words
    words = [card.get("spelling") for card in cards]
    # remove fully non-kanji and empty words
    words = [w for w in words if has_kanji(w)]

    if debug:
        print(words[:5], "\n")
    return words


def has_kanji(word: str) -> bool:
    """
    Returns true iff word is non-empty and contains any kanji
    """
    return bool(word and re.search(r"[一-龯]", word))


def separate_words(words: Iterable[str]) -> DefaultDict[str, Set[str]]:
    """
    Separates words into their component kanji and returns a dict where each component kanji
    links to all words that can be formed from it.

    Non-kanji components (e.g. kana) are not used as keys

    For example, from "今朝 今晩 朝食":
    {
        "今": ["今朝", "今晩"],
        "朝": ["今晩", "朝食"],
        "晩": ["今晩"],
        "食": ["朝食"]
    }
    """
    # for every component kanji, get words that contain that kanji
    components: DefaultDict[str, Set[str]] = defaultdict(set)
    for word in words:
        for char in word:
            # ignore non-kanji characters
            if has_kanji(char):
                components[char].add(word)

    if debug:
        print(list(components.items())[:5], "\n")
    return components


def relate_words(
    words: Iterable[str], components: Dict[str, Iterable[str]]
) -> Dict[str, Set[str]]:
    """
    Returns a dict where each word links to all other words that share at least one component kanji

    For example, from "今朝 今晩 朝食":
    {
        "今朝": ["今晩", "朝食"],
        "今晩": ["今朝"],
        "朝食": ["今朝"]
    }
    """
    # for each word, get words that share any component kanji
    related_words: Dict[str, Set[str]] = {word: set() for word in words}
    for word in words:
        for kanji, compounds in components.items():
            if kanji not in word:
                continue
            related_words[word].update(compounds)

    # remove redundant self-link
    for word, rel_words in related_words.items():
        rel_words.remove(word)

    if debug:
        print(list(related_words.items())[:5], "\n")
    return related_words


def save_to_json(
    save_path: str,
    components: Dict[str, List[str]],
    related_words: Dict[str, List[str]],
) -> None:
    """
    Saves components and related words as fields in a JSON object + file
    """
    with open(save_path, "w", encoding="utf-8") as f:
        obj = {"components": components, "related_words": related_words}
        json.dump(obj, f, ensure_ascii=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Highlight connections between kanji compounds by shared component kanjis"
    )
    parser.add_argument(
        "input_file",
        type=str,
        nargs="?",
        default=argparse.SUPPRESS,  # detect if input is unspecified
        help="path to input file (default 'words.txt', or 'reviews.json' if -j is set)",
    )
    parser.add_argument(
        "-j",
        "--jpdb",
        action="store_true",
        default=False,
        help="if set, treat input file as jpdb export json",
    )
    parser.add_argument(
        "-d",
        "--delimiter",
        type=str,
        default=None,
        help="delimiter when using text file (default None)",
    )
    parser.add_argument(
        "-o",
        "--output_file",
        type=str,
        nargs="?",
        default="output.json",
        help="path to output file (default 'output.json')",
    )
    parser.add_argument(
        "-D",
        "--debug",
        action="store_true",
        default=False,
        help="if set, enable debug prints",
    )
    args = parser.parse_args()
    debug = args.debug
    if debug:
        print(args)

    # set input file based on if user specified file name and jpdb flag
    if hasattr(args, "input_file"):
        input_file = args.input_file
    else:
        input_file = "reviews.json" if args.jpdb else "words.txt"
    delim = args.delimiter
    output_file = args.output_file
    if debug:
        print(input_file, delim, args.jpdb, output_file)

    main(input_file, delim, args.jpdb, output_file)
