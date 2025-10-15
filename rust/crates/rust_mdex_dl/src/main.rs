use rust_mdex_dl::{
    api::{client::ApiClient, download::DownloadClient, search::SearchClient},
    config::load_config,
    logging::init_logging,
};

use log::info;
use miette::{IntoDiagnostic, Result};
use rustyline::DefaultEditor;
use tokio;

#[tokio::main]
async fn main() -> Result<()> {
    // load config
    let cfg = load_config()?;
    init_logging(&cfg.logging);
    info!("Config: {cfg:?}");

    // create clients
    let api = ApiClient::new(&cfg.client)?;
    let searcher = SearchClient::new(api.clone(), cfg.client.language, 10);
    let downloader = DownloadClient::new(&cfg)?;

    // setup i/o with rustyline and get query
    let mut rl = DefaultEditor::new().into_diagnostic()?;
    let query = rl.readline(">> ").into_diagnostic()?;

    // search, fetch and display first page of query
    let results = searcher.search(&query, 0).await?;
    results.display(cfg.client.language);

    // get chosen manga and its chapters
    let manga_index: usize = rl
        .readline(">> ")
        .into_diagnostic()?
        .parse()
        .into_diagnostic()?;

    let manga_index = manga_index - 1; // one-indexed => zero-indexed
    let chosen_manga = results.get(manga_index).expect("invalid index");
    let chapters = searcher.fetch_all_chapters(&chosen_manga).await?;

    // download!
    downloader
        .download_chapters(&api, chapters, chosen_manga, &cfg.images)
        .await?;

    Ok(())
}
