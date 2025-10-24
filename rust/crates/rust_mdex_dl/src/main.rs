use rust_mdex_dl::{
    api::{client::ApiClient, download::DownloadClient, models::Manga, search::SearchClient},
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

#[tokio::main]
async fn main() -> Result<()> {
    // load config
    let cfg = load_config()?;
    init_logging(&cfg.logging);
    info!("Config: {cfg:?}");

    // create clients
    let api = ApiClient::new(&cfg.client)?;
    let searcher = SearchClient::new(api.clone(), cfg.client.language, 200);
    let downloader = DownloadClient::new(&cfg)?;

    // setup i/o with dialoguer and get query
    let query: String = Input!()
        .with_prompt("Enter a manga")
        .interact_text()
        .into_diagnostic()?;

    // search!
    let results = searcher.search(&query, 0).await?;

    if results.data.len() == 0 {
        println!("{}", style("No results found").yellow().italic());
    }

    // display options, get choice
    let mut options = results.display(cfg.client.language);
    options.push(String::from("Next page"));

    let chosen_index = Select!()
        .items(options.as_slice())
        .default(0)
        .interact()
        .into_diagnostic()?;

    // fetch chapters
    let chosen_manga = Manga::from_data(results.data[chosen_index].clone());
    let chapters = searcher.fetch_all_chapters(&chosen_manga).await?;

    // download!
    downloader
        .download_chapters(&api, chapters, chosen_manga, &cfg.images)
        .await?;

    Ok(())
}
