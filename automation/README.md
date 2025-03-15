# GPT Builder Automation

This script automates the process of updating your custom GPT in OpenAI's GPT Builder interface using Playwright.

## Features

- Automatically logs in to your OpenAI account
- Navigates to your specific GPT
- Updates the OpenAPI schema
- Optionally updates the GPT configuration (name, description, instructions)
- Handles existing actions by deleting and recreating them

## Prerequisites

- Node.js (v14 or later)
- npm or yarn

## Setup

1. Install dependencies:
   ```
   npm install
   ```
   or
   ```
   yarn install
   ```

2. Create a `.env` file based on `.env.example`:
   ```
   cp .env.example .env
   ```

3. Edit the `.env` file with your OpenAI credentials and GPT information:
   ```
   OPENAI_EMAIL=your_email@example.com
   OPENAI_PASSWORD=your_password
   GPT_ID=g-your-gpt-id
   GPT_NAME="Your GPT Name"
   OPENAPI_SCHEMA_PATH="../path/to/openapi.yaml"
   CONFIG_JSON_PATH="../path/to/config.json"
   ```

## Usage

Run the script with:

```
npm run update
```

or

```
yarn update
```

### Command Line Options

- `--headless` or `-h`: Run in headless mode (default: false)
- `--schema` or `-s`: Path to OpenAPI schema file (overrides .env setting)
- `--config` or `-c`: Path to GPT config JSON file (overrides .env setting)

Example:
```
npm run update -- --schema=../custom-path/openapi.yaml --headless=true
```

## Important Notes

- This script uses your OpenAI credentials to log in. Keep your `.env` file secure and never commit it to version control.
- The script may break if OpenAI changes their UI. If this happens, you'll need to update the selectors in the script.
- Running the script with `headless=false` (the default) allows you to see what's happening and debug issues.
- OpenAI may have rate limits or security measures that could affect automation. Use responsibly.

## Troubleshooting

- If the script fails to log in, check your credentials in the `.env` file.
- If selectors aren't found, the UI may have changed. Try running with `headless=false` to see what's happening.
- For login issues, you might need to handle 2FA or CAPTCHA manually by setting `headless=false` and interacting with the browser when prompted.

## License

MIT 