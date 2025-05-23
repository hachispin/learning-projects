## Description
A basic CLI app that can search for and download manga from [MangaDex](https://mangadex.org).

### Notes
- Files are saved in a folder called ```mdex_save``` within the same folder of ```mangadex_dl.py```
- This only supports English, but can easily be modified by changing Line 234 according to the [language codes](https://api.mangadex.org/docs/3-enumerations/#language-codes--localization):
```
        if chapter["attributes"]["translatedLanguage"] == "en":
```
- Downloads aren't very fast, so consider using [requests-futures](https://github.com/ross/requests-futures) instead
- ```image_report()``` isn't necessary, but is [recommended](https://api.mangadex.org/docs/04-chapter/retrieving-chapter/#mangadexhome-load-successes-failures-and-retries)
- If you want to extend this in any way, refer to the [docs](https://api.mangadex.org/docs)
