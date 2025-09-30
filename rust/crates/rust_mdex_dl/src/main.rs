mod api;
mod config;
mod deserializers;
mod errors;
mod paths;

use api::{client::ApiClient, endpoints::*};
use config::load_config;

use miette::{self, ErrReport, IntoDiagnostic, Result};
use tokio;
use uuid::Uuid;

use crate::api::models::{Chapter, Manga};

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
    let chapter_uuid = get_valid_uuid(&mut rl)?;
    let api = ApiClient::new(&cfg.client)?;
    let chapter = Chapter::new(&api, chapter_uuid).await?;
    let parent_uuid = chapter.parent_uuid();

    let parent = Manga::new(&api, parent_uuid).await?;
    println!("{parent:?}");

    Ok(())
}
