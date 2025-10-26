use isolang::Language;
use rust_mdex_dl::{
    api::{
        client::ApiClient,
        download::DownloadClient,
        models::Manga,
        search::{SearchClient, SearchResults},
    },
    config::load_config,
    logging::init_logging,
};

use console::style;
use dialoguer::{Input, Select, theme::ColorfulTheme};
use log::info;
use miette::{IntoDiagnostic, Result};
use tokio;

macro_rules! Input {
    () => {
        Input::with_theme(&ColorfulTheme::default())
    };
}

macro_rules! Select {
    () => {
        Select::with_theme(&ColorfulTheme::default())
    };
}

#[derive(PartialEq)]
enum PagePosition {
    Start,
    Middle,
    End,
    All,
}

impl PagePosition {
    fn new(start: u32, end: u32, page: u32) -> Self {
        assert!(start <= end);
        assert!(page >= start && page <= end);

        if start == end {
            return Self::All;
        }

        if page == start && page < end {
            return Self::Start;
        } else if page > start && page < end {
            return Self::Middle;
        } else if page == end {
            return Self::End;
        } else {
            unreachable!();
        }
    }
}

enum PageAction {
    Last,
    Next,
    Choose,
}

impl PageAction {
    fn new(page_pos: PagePosition, next_page_index: usize, chosen_index: usize) -> Self {
        let last_page_index = 0usize;

        if page_pos == PagePosition::Start && chosen_index == next_page_index {
            return PageAction::Next;
        } else if page_pos == PagePosition::Middle && chosen_index == last_page_index {
            return PageAction::Last;
        } else if page_pos == PagePosition::Middle && chosen_index == next_page_index {
            return PageAction::Next;
        } else if page_pos == PagePosition::End && chosen_index == last_page_index {
            return PageAction::Last;
        }
        PageAction::Choose
    }
}

/// Fetches and displays the results using `dialoguer` for the
/// `query` using `searcher` with pagination functionality.
///
/// Returns the selected `Manga`, or `None` if there are no results for the `query`.
async fn manga_search_menu(
    searcher: &SearchClient,
    language: Language,
    query: &str,
) -> Result<Option<Manga>> {
    let mut page = 0u32;
    let mut pages: Vec<SearchResults> = Vec::new();

    let results = searcher.search(query, page).await?;

    if results.total == 0 {
        return Ok(None);
    }

    let total_pages = results.total.div_ceil(SearchClient::MAX_MANGA_PAGINATION);
    pages.reserve(total_pages as usize);
    pages.push(results);

    loop {
        let results_maybe = pages.get(page as usize);

        let results = match results_maybe {
            Some(v) => v,
            None => &searcher.search(query, page).await?,
        };

        let mut options = results.display(language);
        let prompt = format!("Page {}/{}", page + 1, total_pages);

        let page_pos = PagePosition::new(0, total_pages - 1, page);

        match page_pos {
            PagePosition::Start => {
                options.push(style("Next page").to_string());
            }
            PagePosition::Middle => {
                options.insert(0, style("Last page").yellow().to_string());
                options.push(style("Next page").yellow().to_string());
            }
            PagePosition::End => {
                options.insert(0, style("Last page").yellow().to_string());
            }
            PagePosition::All => {}
        }

        // logically, this wouldn't be the index of the "next page" option if
        // it wasn't inserted, however, this is "handled" in `PageAction::new()`
        let next_page = options.len() - 1;

        let chosen_index = Select!()
            .with_prompt(prompt)
            .items(options)
            .default(0)
            .interact()
            .into_diagnostic()?;

        let page_action = PageAction::new(page_pos, next_page, chosen_index);

        match page_action {
            PageAction::Last => page -= 1,
            PageAction::Choose => {
                return Ok(Some(Manga::from_data(results.data[chosen_index].clone())));
            }
            PageAction::Next => page += 1,
        }
    }
}

#[tokio::main]
async fn main() -> Result<()> {
    // load config
    let cfg = load_config()?;
    init_logging(&cfg.logging);
    info!("Config: {cfg:?}");

    // create clients
    let api = ApiClient::new(&cfg.client)?;
    let searcher = SearchClient::new(api.clone(), cfg.client.language);
    let downloader = DownloadClient::new(&cfg)?;

    // get query and search!
    let chosen_manga = loop {
        let query: String = Input!()
            .with_prompt("Enter a manga")
            .interact_text()
            .into_diagnostic()?;

        let chosen = manga_search_menu(&searcher, cfg.client.language, &query).await?;

        match chosen {
            Some(m) => break m,
            None => continue,
        }
    };

    // fetch chapters
    let chapters = searcher.fetch_all_chapters(&chosen_manga).await?;

    // download!
    downloader
        .download_chapters(&api, chapters, chosen_manga, &cfg.images)
        .await?;

    println!();

    Ok(())
}
