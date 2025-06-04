# Adocify

🎯 **AI-powered Markdown to AsciiDoc converter** using DeepSeek Reasoner for intelligent documentation transformation.

## Overview

Adocify is a TypeScript/Node.js CLI tool that converts Markdown files to AsciiDoc format using AI analysis. It reads your project structure, understands the context of each module, and generates high-quality AsciiDoc files following a consistent style guide.

## Features

- 🤖 **AI-Powered Conversion**: Uses DeepSeek Reasoner for intelligent Markdown → AsciiDoc transformation
- 📚 **Context-Aware**: Analyzes module files and structure for better conversion quality
- 🎨 **Style Consistency**: Follows a reference AsciiDoc style guide for uniform output
- ⚡ **Concurrent Processing**: Parallel conversion with configurable concurrency limits
- 🛡️ **Production-Ready**: Comprehensive error handling, logging, and validation
- 🎯 **CLI Interface**: Easy-to-use command-line interface with multiple options

## Installation

### Prerequisites

- Node.js 18.0.0 or higher
- DeepSeek API key (set as `DEEPSEEK_API_KEY` environment variable)

### Setup

```bash
# Install dependencies
npm install

# Build the project
npm run build

# Check environment
npm start check
```

## Usage

### Basic Conversion

```bash
# Convert all README.md files in the project
npm start convert

# Or using the built binary
./dist/index.js convert
```

### Advanced Options

```bash
# Convert with custom concurrency (default: 5)
npm start convert --concurrency 3

# Use verbose output for detailed logging
npm start convert --verbose

# Convert specific files using glob pattern
npm start convert --pattern "src/**/README.md"

# Use custom style guide
npm start convert --style-guide "docs/style.adoc"
```

### Environment Check

```bash
# Verify setup and dependencies
npm start check
```

## Configuration

### Environment Variables

- `DEEPSEEK_API_KEY`: Your DeepSeek API key (required)

### CLI Options

| Option              | Description                      | Default              |
| ------------------- | -------------------------------- | -------------------- |
| `--concurrency, -c` | Number of concurrent conversions | 5                    |
| `--verbose, -v`     | Enable detailed output           | false                |
| `--pattern, -p`     | Glob pattern for markdown files  | `**/README.md`       |
| `--style-guide, -s` | Path to AsciiDoc style guide     | `incron/README.adoc` |

## Development

### Scripts

```bash
npm run dev          # Run in development mode with tsx
npm run build        # Compile TypeScript to JavaScript
npm run clean        # Remove build artifacts
npm run lint         # Run ESLint
npm run format       # Format code with Prettier
npm run type-check   # Type check without emitting files
```

### Project Structure

```
adocify/
├── src/
│   └── index.ts     # Main CLI application
├── dist/            # Compiled JavaScript output
├── package.json     # Project configuration
├── tsconfig.json    # TypeScript configuration
├── eslint.config.js # ESLint configuration
└── .prettierrc      # Prettier configuration
```

## How It Works

1. **Discovery**: Scans for Markdown files using glob patterns
2. **Context Analysis**: Reads module files and structure for each README.md
3. **Style Guide Loading**: Uses reference AsciiDoc file for consistent formatting
4. **AI Conversion**: Sends context and content to DeepSeek Reasoner API
5. **Parallel Processing**: Converts multiple files concurrently with rate limiting
6. **Output Generation**: Writes converted AsciiDoc files alongside originals

## API Integration

Adocify uses the OpenAI-compatible DeepSeek API:

- **Endpoint**: `https://api.deepseek.com/v1`
- **Model**: `deepseek-chat`
- **Temperature**: 0.2 (for consistent output)
- **Max Tokens**: 4096

## Error Handling

- ✅ Graceful handling of missing files
- ✅ API rate limit management
- ✅ Comprehensive logging with colored output
- ✅ Process isolation to prevent failures cascading
- ✅ Environment validation before execution

## Examples

### Converting Documentation

```bash
# Convert all module READMEs with verbose output
npm start convert --verbose

# Convert specific documentation directory
npm start convert --pattern "docs/**/*.md"

# Use different concurrency for large projects
npm start convert --concurrency 10
```

### Sample Output

```
🚀 Starting Markdown to AsciiDoc conversion
📖 Using style guide: incron/README.adoc
📚 Found 12 modules to convert
🔄 Processing module: git
✅ Converted git/README.md to git/README.adoc
🔄 Processing module: imgtag
✅ Converted imgtag/README.md to imgtag/README.adoc
🎉 Conversion completed in 42.35s
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## License

MIT License - see LICENSE file for details.
