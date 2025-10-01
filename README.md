# Overview

Takes in either:

1.  a txt file containing words (default 'words.txt')
2.  a json file from jpdb's data export (default 'reviews.json')

    -   for details, see read_from_jpdb()

and returns a JSON file containing two objects:

1. Component kanji -> all words containing it

    - Non-kanji components (e.g. kana) are not used as keys

2. Words -> other words that share any kanji

    - Partial-kanji words are included as keys
    - Non-kanji characters (e.g. kana) are not considered

Fully non-kanji (kana, alphanumeric, etc.) words are ignored but partial-kanji words are still processed to allow words like 楽しい

## Example

For example, inputting "今朝 今晩 朝食 食べる 楽しい かな english!" in 'words.txt' should return in 'output.json':

```json
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
```

(note lack of "かな" and "english!")

Running with no arguments will take in 'words.txt' and output 'output.json'

## CLI help menu

```
$ python hikari.py --help
usage: hikari.py [-h] [-j] [-d DELIMITER] [-o [OUTPUT_FILE]] [-D] [input_file]

Highlight connections between kanji compounds by shared component kanjis

positional arguments:
  input_file            path to input file (default 'words.txt', or 'reviews.json'
                        if -j is set)

options:
  -h, --help            show this help message and exit
  -j, --jpdb            if set, treat input file as jpdb export json
  -d DELIMITER, --delimiter DELIMITER
                        delimiter when using text file (default None)
  -o [OUTPUT_FILE], --output_file [OUTPUT_FILE]
                        path to output file (default 'output.json')
  -D, --debug           if set, enable debug prints
```
