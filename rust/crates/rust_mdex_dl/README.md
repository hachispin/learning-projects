# rust-mdex-dl

## Preamble

This is a Rust rewrite of my Python project, [mdex_tool](/python/mdex_tool). Notably, this
project is quite a bit heavier since it uses large dependencies like [tokio](https://docs.rs/tokio/latest/tokio/).

Comparing dependency count: this project has 20 dependencies, while the original Python
version has only three. However, I would say that this project is definitely more polished.

## Description

An easy-to-use CLI tool (using [dialoguer](https://docs.rs/dialoguer/latest/dialoguer/)) written in Rust
for downloading manga from [MangaDex](https://mangadex.org/). Searching functionality is also included
to make finding manga more convenient.

You may want to edit the [config file](./rust_mdex_dl/config.toml) for options such as
choosing your desired language (default: EN), or lowering image quality for slower connections.

## Usage

0) Either use the binary or build this project
1) Run the program
2) Enter the name of a manga
3) Select the manga from the provided search results
4) Wait for the manga to be downloaded

## To-do

- [ ] Allow downloading of specific chapters
- [ ] Refactor pagination logic
- [ ] Maybe try not abandoning this project?
