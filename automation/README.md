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

3. Edit the `.env` file with your OpenAI credentials:
   
   For Google authentication (recommended):
   ```
   OPENAI_EMAIL=your_google_email@gmail.com
   # Password not needed for Google authentication
   GPT_ID=g-your-gpt-id
   GPT_NAME="Your GPT Name"
   OPENAPI_SCHEMA_PATH="../path/to/openapi.yaml"
   CONFIG_JSON_PATH="../path/to/config.json"
   ```
   
   For direct OpenAI authentication:
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

### Authentication Methods

The script supports two authentication methods:

1. **Google Authentication** (default): 
   - The script will open a browser window and navigate to OpenAI's login page
   - It will click "Continue with Google"
   - You'll need to manually log in with your Google account
   - After successful login, the script will continue automatically

2. **Direct OpenAI Authentication**:
   - To use this method, add the `--auth-method=direct` flag
   - You must provide both email and password in the `.env` file
   - Example: `node update-gpt.js --auth-method=direct`

### Command Line Options

- `--headless=true`: Run in headless mode (no visible browser)
- `--schema=path/to/schema.yaml`: Use a different OpenAPI schema file
- `--config=path/to/config.json`: Use a different GPT config file
- `--wait-for-captcha=false`: Don't wait for manual CAPTCHA solving (not recommended)
- `--auth-method=direct|google`: Choose authentication method (default: google)

Example with options:
```bash
node update-gpt.js --headless=false --schema=../gpt_config/openapi.yaml --auth-method=google
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