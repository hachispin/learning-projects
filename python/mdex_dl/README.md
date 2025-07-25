# `mdex_dl` (_Rewrite in progress!_)

Only CLI left to go.

## Usage

**WIP**

## Description

A basic CLI app that can search for and download manga from [MangaDex](https://mangadex.org).

### Ratelimit handling

Example debug level log; simplified for brevity. This is calling the `GET /manga/random` endpoint.

This endpoint has a ratelimit of [60 requests per minute](https://api.mangadex.org/docs/2-limitations/#endpoint-specific-rate-limits).

```
15:26 Request #61
15:26 [urllib3.connectionpool] https://api.mangadex.org:443 "GET /manga/random HTTP/1.1" 429 174
15:26 [mdex_dl.api.client] Ratelimited (received status code 429)
15:26 [mdex_dl.api.client] X-RateLimit-Retry-After = 1753190169
15:26 [mdex_dl.api.client] Time to sleep: 42 seconds
16:08 [urllib3.connectionpool] Resetting dropped connection: api.mangadex.org
16:08 [urllib3.connectionpool] https://api.mangadex.org:443 "GET /manga/random HTTP/1.1" 200 None
16:08 [mdex_dl.api.search] Muni no Ichigeki
```

Full log [here](https://gist.github.com/hachispin/845e71905a2ae6e4c0be989ea07a8750) along with the [code used](https://gist.github.com/hachispin/5b6895ae2c7fd02774352f3c789829be).

### Config

**WIP**

## Notes

**WIP**

## To-do

- [ ] **Give better feedback on when chapters can't be downloaded**
- [x] Add a config file &rarr; _uses config.toml_
- [ ] Allow sorting by tags and other characteristics of note
- [x] Switch to [requests-futures](https://github.com/ross/requests-futures) or pipe through `curl` for faster download speeds &rarr; _uses [PyCurl](https://github.com/pycurl/pycurl)_
