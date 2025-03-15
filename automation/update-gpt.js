const { chromium } = require('playwright');
const fs = require('fs-extra');
const path = require('path');
const dotenv = require('dotenv');
const yargs = require('yargs/yargs');
const { hideBin } = require('yargs/helpers');
const readline = require('readline');

// Load environment variables
dotenv.config();

// Parse command line arguments
const argv = yargs(hideBin(process.argv))
  .option('headless', {
    alias: 'h',
    type: 'boolean',
    description: 'Run in headless mode',
    default: false
  })
  .option('schema', {
    alias: 's',
    type: 'string',
    description: 'Path to OpenAPI schema file',
    default: process.env.OPENAPI_SCHEMA_PATH
  })
  .option('config', {
    alias: 'c',
    type: 'string',
    description: 'Path to GPT config JSON file',
    default: process.env.CONFIG_JSON_PATH
  })
  .option('wait-for-captcha', {
    alias: 'w',
    type: 'boolean',
    description: 'Wait for manual CAPTCHA solving',
    default: true
  })
  .help()
  .alias('help', 'h')
  .argv;

// Configuration
const config = {
  openaiEmail: process.env.OPENAI_EMAIL,
  openaiPassword: process.env.OPENAI_PASSWORD,
  gptId: process.env.GPT_ID,
  gptName: process.env.GPT_NAME,
  openApiSchemaPath: argv.schema,
  configJsonPath: argv.config,
  headless: argv.headless,
  waitForCaptcha: argv['wait-for-captcha']
};

// Validate configuration
if (!config.openaiEmail || !config.openaiPassword) {
  console.error('Error: OpenAI credentials not found. Please set OPENAI_EMAIL and OPENAI_PASSWORD in .env file.');
  process.exit(1);
}

if (!config.gptId) {
  console.error('Error: GPT ID not found. Please set GPT_ID in .env file.');
  process.exit(1);
}

// Function to prompt for 2FA code
function prompt2FACode() {
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
  });

  return new Promise((resolve) => {
    rl.question('Enter the 2FA code sent to your email/phone: ', (code) => {
      rl.close();
      resolve(code.trim());
    });
  });
}

// Function to prompt for manual CAPTCHA solving
function promptForCaptcha() {
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
  });

  return new Promise((resolve) => {
    rl.question('CAPTCHA detected. Please solve it manually in the browser window and press Enter when done...', () => {
      rl.close();
      resolve();
    });
  });
}

// Main function
async function updateGpt() {
  console.log('Starting GPT update automation...');
  
  // Read the OpenAPI schema file
  let openApiSchema;
  try {
    openApiSchema = await fs.readFile(config.openApiSchemaPath, 'utf8');
    console.log(`Successfully read OpenAPI schema from ${config.openApiSchemaPath}`);
  } catch (error) {
    console.error(`Error reading OpenAPI schema: ${error.message}`);
    process.exit(1);
  }
  
  // Read the config JSON file if provided
  let configJson;
  if (config.configJsonPath) {
    try {
      configJson = await fs.readFile(config.configJsonPath, 'utf8');
      configJson = JSON.parse(configJson);
      console.log(`Successfully read config JSON from ${config.configJsonPath}`);
    } catch (error) {
      console.error(`Error reading config JSON: ${error.message}`);
      process.exit(1);
    }
  }
  
  // Launch browser
  console.log('Launching browser...');
  const browser = await chromium.launch({
    headless: config.headless
  });
  
  // Create a new context with viewport
  const context = await browser.newContext({
    viewport: { width: 1280, height: 800 }
  });
  
  // Create a new page
  const page = await context.newPage();
  
  try {
    // Navigate to OpenAI login page
    console.log('Navigating to OpenAI login page...');
    await page.goto('https://chat.openai.com/auth/login');
    
    // Wait for the login button and click it
    await page.waitForSelector('button:has-text("Log in")');
    await page.click('button:has-text("Log in")');
    
    // Wait for email input and enter email
    console.log('Entering email...');
    await page.waitForSelector('input[name="username"]');
    await page.fill('input[name="username"]', config.openaiEmail);
    await page.click('button[type="submit"]');
    
    // Check for CAPTCHA
    const hasCaptcha = await page.locator('iframe[title="reCAPTCHA"]').count() > 0;
    if (hasCaptcha) {
      console.log('CAPTCHA detected!');
      if (config.waitForCaptcha) {
        console.log('Please solve the CAPTCHA manually in the browser window...');
        await promptForCaptcha();
      } else {
        throw new Error('CAPTCHA detected but automatic solving is not implemented. Use --wait-for-captcha=true to solve manually.');
      }
    }
    
    // Wait for password input and enter password
    console.log('Entering password...');
    await page.waitForSelector('input[name="password"]');
    await page.fill('input[name="password"]', config.openaiPassword);
    await page.click('button[type="submit"]');
    
    // Check for CAPTCHA again
    const hasCaptchaAfterPassword = await page.locator('iframe[title="reCAPTCHA"]').count() > 0;
    if (hasCaptchaAfterPassword) {
      console.log('CAPTCHA detected after password entry!');
      if (config.waitForCaptcha) {
        console.log('Please solve the CAPTCHA manually in the browser window...');
        await promptForCaptcha();
      } else {
        throw new Error('CAPTCHA detected but automatic solving is not implemented. Use --wait-for-captcha=true to solve manually.');
      }
    }
    
    // Check for 2FA
    try {
      // Wait a short time to see if 2FA is required
      await page.waitForSelector('input[inputmode="numeric"]', { timeout: 5000 });
      console.log('2FA authentication required...');
      
      // Prompt for 2FA code
      const code = await prompt2FACode();
      
      // Enter the 2FA code
      await page.fill('input[inputmode="numeric"]', code);
      await page.click('button[type="submit"]');
    } catch (error) {
      // No 2FA required, continue
      console.log('No 2FA required or already handled by browser.');
    }
    
    // Wait for the chat page to load
    console.log('Waiting for chat page to load...');
    await page.waitForURL('https://chat.openai.com/**', { timeout: 30000 });
    
    // Navigate to the GPT Builder page for the specific GPT
    console.log(`Navigating to GPT Builder for ${config.gptName}...`);
    await page.goto(`https://chat.openai.com/g/${config.gptId}/builder`);
    
    // Wait for the GPT Builder page to load
    await page.waitForSelector('div[role="tab"]:has-text("Configure")', { timeout: 10000 });
    
    // Click on the Configure tab if not already active
    const configureTab = await page.$('div[role="tab"]:has-text("Configure")');
    const isConfigureTabActive = await configureTab.evaluate(el => el.getAttribute('aria-selected') === 'true');
    if (!isConfigureTabActive) {
      await configureTab.click();
      await page.waitForTimeout(1000); // Wait for tab to become active
    }
    
    // Update the GPT configuration if provided
    if (configJson) {
      console.log('Updating GPT configuration...');
      
      // Update name if different
      const nameInput = await page.$('input[placeholder="Name your GPT"]');
      const currentName = await nameInput.inputValue();
      if (currentName !== configJson.name) {
        await nameInput.fill('');
        await nameInput.fill(configJson.name);
        console.log(`Updated GPT name to: ${configJson.name}`);
      }
      
      // Update description if different
      const descriptionInput = await page.$('textarea[placeholder="Write a description"]');
      const currentDescription = await descriptionInput.inputValue();
      if (currentDescription !== configJson.description) {
        await descriptionInput.fill('');
        await descriptionInput.fill(configJson.description);
        console.log(`Updated GPT description`);
      }
      
      // Update instructions if different
      const instructionsInput = await page.$('div[data-slate-editor="true"]');
      // This is more complex as it's a rich text editor, so we'll use a workaround
      await page.evaluate((instructions) => {
        const editor = document.querySelector('div[data-slate-editor="true"]');
        if (editor) {
          // Clear the editor
          editor.innerHTML = '';
          
          // Create a new text node with the instructions
          const textNode = document.createTextNode(instructions);
          
          // Append the text node to the editor
          editor.appendChild(textNode);
          
          // Dispatch an input event to trigger any listeners
          editor.dispatchEvent(new Event('input', { bubbles: true }));
        }
      }, configJson.instructions);
      console.log(`Updated GPT instructions`);
    }
    
    // Click on the Actions tab
    console.log('Navigating to Actions tab...');
    await page.click('div[role="tab"]:has-text("Actions")');
    await page.waitForTimeout(1000); // Wait for tab to become active
    
    // Check if there's an existing action
    const hasExistingAction = await page.$$eval('button:has-text("Delete")', buttons => buttons.length > 0);
    
    if (hasExistingAction) {
      // Delete the existing action
      console.log('Deleting existing action...');
      await page.click('button:has-text("Delete")');
      
      // Confirm deletion
      await page.waitForSelector('button:has-text("Delete action")');
      await page.click('button:has-text("Delete action")');
      await page.waitForTimeout(1000); // Wait for deletion to complete
    }
    
    // Add a new action
    console.log('Adding new action with updated OpenAPI schema...');
    await page.click('button:has-text("Add action")');
    
    // Wait for the action modal to appear
    await page.waitForSelector('div[role="dialog"]');
    
    // Click on "Upload an OpenAPI schema"
    await page.click('button:has-text("Upload an OpenAPI schema")');
    
    // Wait for the file input to be available
    const fileInput = await page.waitForSelector('input[type="file"]');
    
    // Create a temporary file with the OpenAPI schema
    const tempFilePath = path.join(__dirname, 'temp-openapi.yaml');
    await fs.writeFile(tempFilePath, openApiSchema);
    
    // Upload the file
    await fileInput.setInputFiles(tempFilePath);
    
    // Wait for the upload to complete
    await page.waitForSelector('text=Successfully uploaded');
    
    // Click the Save button
    await page.click('button:has-text("Save")');
    
    // Wait for the action to be saved
    await page.waitForSelector('text=Action saved successfully', { timeout: 10000 });
    console.log('Action saved successfully!');
    
    // Save the GPT
    console.log('Saving GPT...');
    await page.click('button:has-text("Save")');
    
    // Wait for the save to complete
    await page.waitForSelector('text=GPT updated', { timeout: 10000 });
    console.log('GPT updated successfully!');
    
    // Clean up the temporary file
    await fs.remove(tempFilePath);
    
    // Success!
    console.log('GPT update automation completed successfully!');
  } catch (error) {
    console.error(`Error during automation: ${error.message}`);
    console.error(error.stack);
  } finally {
    // Close the browser
    await browser.close();
  }
}

// Run the main function
updateGpt().catch(console.error); 