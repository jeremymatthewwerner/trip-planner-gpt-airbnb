import re
import os

def redact_sensitive_info(text):
    # Redact API keys and other sensitive patterns
    patterns = [
        (r'sk-[a-zA-Z0-9-_]{32,}', '[OPENAI_API_KEY_REDACTED]'),
        (r'[a-f0-9]{32}(?:[a-f0-9]{8})?', '[API_KEY_REDACTED]'),
        (r'[A-Za-z0-9-_]{32,}(?:\.?[A-Za-z0-9-_]{8,}){1,2}', '[POSSIBLE_API_KEY_REDACTED]'),
    ]
    
    for pattern, replacement in patterns:
        text = re.sub(pattern, replacement, text)
    return text

def copy_and_redact_file(source_path, dest_path):
    if not os.path.exists(source_path):
        print(f"Source file {source_path} not found")
        return
    
    try:
        with open(source_path, 'r', encoding='utf-8') as source:
            content = source.read()
            
        redacted_content = redact_sensitive_info(content)
        
        with open(dest_path, 'w', encoding='utf-8') as dest:
            dest.write(redacted_content)
            
        print(f"Successfully copied and redacted file to {dest_path}")
    except Exception as e:
        print(f"Error processing file: {e}")

if __name__ == "__main__":
    source = ".specstory/history/2025-03-14_23-34-project-status-check.md"
    destination = "cursor-agent-chat-log.md"
    copy_and_redact_file(source, destination) 