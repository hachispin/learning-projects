mod api;
mod config;
mod deserializers;
mod errors;
mod paths;

use api::{
    client::ApiClient,
    downloader::{self, ChapterCdnInfo},
    endpoints::*,
};
use config::load_config;

use std::time::Instant;

use miette::{self, ErrReport, IntoDiagnostic, Result};
use tokio;
use uuid::Uuid;

/// Continuously prompts the user until a valid UUID is entered.
fn get_valid_uuid(rl: &mut rustyline::DefaultEditor) -> Result<Uuid> {
    loop {
        let input = rl.readline(">> ").into_diagnostic()?;
        rl.add_history_entry(&input).into_diagnostic()?;

        let uuid = Uuid::parse_str(&input);

        if let Ok(v) = uuid {
            return Ok(v);
        }

        println!("{:?}", ErrReport::from_err(uuid.unwrap_err()));
    }
}

#[tokio::main]
async fn main() -> Result<()> {
    miette::set_panic_hook();
    let cfg = load_config()?;
    println!("{cfg:?}");

    let mut rl = rustyline::DefaultEditor::new().into_diagnostic()?;
    let manga_uuid = get_valid_uuid(&mut rl)?;
    let api = ApiClient::new(&cfg.client)?;

    let cdn_json = api.get_ok_json(Endpoint::GetChapterCdn(manga_uuid)).await?;

    let cdn_data = ChapterCdnInfo::new(&cdn_json);
    let image_urls = cdn_data.construct_image_urls(false)?;

    let start = Instant::now();
    downloader::download_images(&image_urls, &cfg).await?;
    let elapsed = Instant::now() - start;

    println!("milliseconds: {}", elapsed.as_millis());

    Ok(())
}
