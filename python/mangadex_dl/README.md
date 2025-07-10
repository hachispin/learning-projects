## Description
A basic CLI app that can search for and download manga from [MangaDex](https://mangadex.org).


This program assumes that **chapters are labeled sensibly**. (e.g chapters numbers are, well numbers, and don't reset per-volume)

Otherwise, they're completely ignored as per Line 239:
```
    for chapter in chapters:
        ...
        if chap is None or not chap.replace(".", "").isdigit():
            continue
        ...
```
### Notes
- Files are saved in a directory called ```mdex_save``` with the same parent as ```mangadex_dl.py```
- This only supports English, but can easily be modified by changing Line 234 according to the [language codes](https://api.mangadex.org/docs/3-enumerations/#language-codes--localization):
```
    for chapter in r.json()["data"]:
        ...
        if chapter["attributes"]["translatedLanguage"] == "en":
        ...
```
- Downloads aren't very fast, so consider using [requests-futures](https://github.com/ross/requests-futures) instead
- ```image_report()``` isn't necessary, but is [recommended](https://api.mangadex.org/docs/04-chapter/retrieving-chapter/#mangadexhome-load-successes-failures-and-retries)
- If you want to extend this in any way, refer to the [docs](https://api.mangadex.org/docs)
