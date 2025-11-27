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

use console::{Term, style};
use dialoguer::{Confirm, Input, Select, theme::ColorfulTheme};
use log::info;
use miette::{IntoDiagnostic, Result};

macro_rules! Input {
    () => {
        Input::with_theme(&ColorfulTheme::default())
    };
}

macro_rules! Select {
    () => {
        Select::with_theme(&ColorfulTheme::default()).default(0)
    };
}

macro_rules! Confirm {
    () => {
        Confirm::with_theme(&ColorfulTheme::default())
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
        if start == end {
            return Self::All;
        }

        if page == start && page < end {
            Self::Start
        } else if page > start && page < end {
            Self::Middle
        } else {
            Self::End
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
        let next = next_page_index;
        let last = 0usize;

        match (page_pos, chosen_index) {
            (PagePosition::Start, i) if i == next => Self::Next,
            (PagePosition::Middle, i) if i == last => Self::Last,
            (PagePosition::Middle, i) if i == next => Self::Next,
            (PagePosition::End, i) if i == last => Self::Last,
            _ => Self::Choose, 
        }
    }
}

/// Fetches and displays the results using `dialoguer` for the
/// `query` using `searcher` with pagination functionality.
///
/// Returns the selected `Manga`, or `None` if there's no results/user exits.
async fn manga_search_menu(
    searcher: &SearchClient,
    language: Language,
    query: &str,
    out: &Term,
) -> Result<Option<Manga>> {
    let mut page = 0u32;
    let mut pages: Vec<SearchResults> = Vec::new();

    let results = searcher.search(query, page).await?;

    if results.total == 0 {
        out.write_line(&style("No results found").yellow().italic().to_string())
            .into_diagnostic()?;

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
        let mut offset = 0usize; // for when "last page" is inserted at index 0

        match page_pos {
            PagePosition::Start => {
                options.push(style("Next page").yellow().to_string());
            }
            PagePosition::Middle => {
                options.insert(0, style("Last page").yellow().to_string());
                options.push(style("Next page").yellow().to_string());
                offset = 1;
            }
            PagePosition::End => {
                options.insert(0, style("Last page").yellow().to_string());
                offset = 1;
            }
            PagePosition::All => {}
        }

        // logically, this wouldn't be the index of the "next page" option if
        // it wasn't inserted, however, this is "handled" in `PageAction::new()`
        let next_page = options.len() - 1;

        let chosen_index = Select!()
            .with_prompt(prompt)
            .items(options)
            .interact_opt() // user can exit with 'Esc'/'q'
            .into_diagnostic()?;

        let Some(chosen_index) = chosen_index else {
            return Ok(None);
        };

        let page_action = PageAction::new(page_pos, next_page, chosen_index);

        match page_action {
            PageAction::Last => page -= 1,
            PageAction::Next => page += 1,
            PageAction::Choose => {
                return Ok(Some(Manga::from_data(
                    results.data[chosen_index - offset].clone(),
                )));
            }
        }
    }
}

#[tokio::main]
async fn main() -> Result<()> {
    // load config
    let cfg = load_config()?;
    init_logging(&cfg.logging);
    info!("Config: {cfg:?}");

    // stdout
    let out = Term::stdout();

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

        let chosen = manga_search_menu(&searcher, cfg.client.language, &query, &out).await?;

        if let Some(v) = chosen {
            break v;
        }

        if !Confirm!()
            .with_prompt("Search again?")
            .interact()
            .into_diagnostic()?
        {
            return Ok(());
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
