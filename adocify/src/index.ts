#!/usr/bin/env node

import fs from 'fs/promises';
import path from 'path';
import { glob } from 'glob';
import OpenAI from 'openai';
import pLimit from 'p-limit';
import { Command } from 'commander';
import chalk from 'chalk';

// Configuration constants
const CONFIG = {
  API: {
    BASE_URL: 'https://api.deepseek.com/v1',
    MODEL_NAME: 'deepseek-chat',
    TEMPERATURE: 0.2,
    MAX_TOKENS: 4096,
  },
  DEFAULTS: {
    STYLE_GUIDE_PATH: 'incron/README.adoc',
    CONCURRENCY_LIMIT: 5,
    PATTERN: '**/README.md',
  },
  IGNORE_PATTERNS: [
    '**/node_modules/**',
    '**/vendor/**',
    '**/.git/**',
    '**/.mypy_cache/**',
    '**/.ropeproject/**',
    '**/.ruff_cache/**',
  ],
} as const;

// Types
interface ConversionOptions {
  concurrency: number;
  verbose: boolean;
  pattern: string;
  styleGuide: string;
  directory: string;
}

interface ConversionContext {
  markdown: string;
  styleGuide: string;
  moduleName: string;
  moduleFiles: string[];
}

interface ConversionResult {
  success: boolean;
  moduleName: string;
  outputPath?: string;
  error?: string;
}

// Environment validation
class Environment {
  private static _apiKey: string | null = null;

  static get apiKey(): string {
    if (this._apiKey === null) {
      const key = process.env['DEEPSEEK_API_KEY'];
      if (!key) {
        console.error(chalk.red('❌ DEEPSEEK_API_KEY environment variable is not set'));
        process.exit(1);
      }
      this._apiKey = key;
    }
    return this._apiKey;
  }

  static validate(): void {
    // Trigger validation by accessing apiKey
    this.apiKey;
  }
}

// Logger utility
class Logger {
  static info(message: string): void {
    console.log(chalk.blue(`ℹ️ ${message}`));
  }

  static success(message: string): void {
    console.log(chalk.green(`✅ ${message}`));
  }

  static warning(message: string): void {
    console.warn(chalk.yellow(`⚠️ ${message}`));
  }

  static error(message: string): void {
    console.error(chalk.red(`❌ ${message}`));
  }

  static processing(message: string): void {
    console.log(chalk.blue(`🔄 ${message}`));
  }

  static verbose(message: string, isVerbose: boolean): void {
    if (isVerbose) {
      console.log(chalk.gray(`   ${message}`));
    }
  }
}

// File operations utility
class FileUtils {
  static async readSafe(filePath: string): Promise<string> {
    try {
      return await fs.readFile(filePath, 'utf-8');
    } catch (error) {
      Logger.warning(`Could not read file ${filePath}: ${(error as Error).message}`);
      return '';
    }
  }

  static async getModuleFiles(modulePath: string): Promise<string[]> {
    try {
      const files = await glob(path.join(modulePath, '*'), {
        nodir: true,
        ignore: ['**/README.md', '**/README.adoc', '**/node_modules/**'],
      });
      return files.map(file => path.basename(file));
    } catch (error) {
      Logger.warning(`Could not list files in ${modulePath}: ${(error as Error).message}`);
      return [];
    }
  }

  static async writeResult(filePath: string, content: string): Promise<void> {
    await fs.writeFile(filePath, content, 'utf-8');
  }
}

// AI service
class AIConverter {
  private readonly client: OpenAI;

  constructor() {
    this.client = new OpenAI({
      baseURL: CONFIG.API.BASE_URL,
      apiKey: Environment.apiKey,
    });
  }

  async convert(context: ConversionContext): Promise<string> {
    const systemMessage = this.buildSystemMessage(context);
    const userMessage = this.buildUserMessage(context);

    try {
      const response = await this.client.chat.completions.create({
        model: CONFIG.API.MODEL_NAME,
        messages: [
          { role: 'system', content: systemMessage },
          { role: 'user', content: userMessage },
        ],
        temperature: CONFIG.API.TEMPERATURE,
        max_tokens: CONFIG.API.MAX_TOKENS,
      });

      return response.choices[0]?.message?.content?.trim() || '';
    } catch (error) {
      throw new Error(`API error for ${context.moduleName}: ${(error as Error).message}`);
    }
  }

  private buildSystemMessage(context: ConversionContext): string {
    return `You are an expert documentation engineer specializing in converting Markdown to AsciiDoc.
Follow these guidelines:
1. Use the provided style guide for structure and formatting
2. Preserve all technical content and code examples exactly
3. Convert Markdown syntax to AsciiDoc equivalents
4. Maintain all links, images, and references
5. Add necessary AsciiDoc directives (like :toc:) where appropriate

Style Guide:
${context.styleGuide}

Module Context:
- Name: ${context.moduleName}
- Files: ${context.moduleFiles.join(', ') || 'No additional files'}`;
  }

  private buildUserMessage(context: ConversionContext): string {
    return `Convert the following README.md to README.adoc using the specified style and context:

${context.markdown}`;
  }
}

// Main converter service
class MarkdownConverter {
  private readonly aiConverter: AIConverter;

  constructor() {
    this.aiConverter = new AIConverter();
  }

  async processModule(
    mdPath: string,
    styleGuide: string,
    options: Pick<ConversionOptions, 'verbose' | 'directory'>
  ): Promise<ConversionResult> {
    const moduleDir = path.dirname(mdPath);
    const moduleName = path.basename(moduleDir);
    const absoluteModuleDir = path.resolve(options.directory, moduleDir);
    const adocPath = path.join(moduleDir, 'README.adoc');
    const absoluteAdocPath = path.resolve(options.directory, adocPath);

    Logger.processing(`Processing module: ${moduleName} (${absoluteModuleDir})`);

    try {
      const absoluteMdPath = path.resolve(options.directory, mdPath);
      const markdown = await FileUtils.readSafe(absoluteMdPath);
      if (!markdown.trim()) {
        Logger.warning(`Skipping empty README.md in ${moduleName} (${absoluteModuleDir})`);
        return { success: false, moduleName, error: 'Empty markdown file' };
      }

      const moduleFiles = await FileUtils.getModuleFiles(absoluteModuleDir);
      const context: ConversionContext = {
        markdown,
        styleGuide,
        moduleName,
        moduleFiles,
      };

      const asciidoc = await this.aiConverter.convert(context);

      if (!asciidoc.trim()) {
        Logger.warning(`No content generated for ${moduleName} (${absoluteModuleDir}), skipping`);
        return { success: false, moduleName, error: 'No content generated' };
      }

      await FileUtils.writeResult(absoluteAdocPath, asciidoc);
      Logger.success(`Converted ${absoluteMdPath} to ${absoluteAdocPath}`);
      Logger.verbose(`Generated ${asciidoc.length} characters`, options.verbose);

      return { success: true, moduleName, outputPath: absoluteAdocPath };
    } catch (error) {
      const absoluteMdPath = path.resolve(options.directory, mdPath);
      const errorMessage = `Failed to process ${absoluteMdPath}: ${(error as Error).message}`;
      Logger.error(errorMessage);
      return { success: false, moduleName, error: errorMessage };
    }
  }

  async convertAll(options: ConversionOptions): Promise<ConversionResult[]> {
    Logger.info('Starting Markdown to AsciiDoc conversion');
    Logger.info(`Target directory: ${path.resolve(options.directory)}`);
    const startTime = Date.now();

    const styleGuide = await this.loadStyleGuide(options.styleGuide, options.verbose, options.directory);
    if (!styleGuide) {
      throw new Error(`Style guide not found at ${options.styleGuide}`);
    }

    const mdFiles = await this.findMarkdownFiles(options.pattern, options.styleGuide, options.directory);
    if (mdFiles.length === 0) {
      Logger.info('No README.md files found');
      return [];
    }

    Logger.info(`Found ${mdFiles.length} modules to convert`);
    if (options.verbose) {
      mdFiles.forEach(file => {
        const absolutePath = path.resolve(options.directory, file);
        Logger.verbose(absolutePath, true);
      });
    }

    const results = await this.processFilesWithConcurrency(mdFiles, styleGuide, options);

    const duration = ((Date.now() - startTime) / 1000).toFixed(2);
    const successful = results.filter(r => r.success).length;
    Logger.success(
      `Conversion completed in ${duration}s (${successful}/${results.length} successful)`
    );

    return results;
  }

  private async loadStyleGuide(styleGuidePath: string, verbose: boolean, directory: string): Promise<string> {
    const absoluteStyleGuidePath = path.resolve(directory, styleGuidePath);
    const styleGuide = await FileUtils.readSafe(absoluteStyleGuidePath);
    if (!styleGuide.trim()) {
      Logger.error(`Style guide not found at ${absoluteStyleGuidePath}`);
      return '';
    }

    Logger.verbose(`Using style guide: ${absoluteStyleGuidePath}`, verbose);
    return styleGuide;
  }

  private async findMarkdownFiles(pattern: string, styleGuidePath: string, directory: string): Promise<string[]> {
    const absoluteDirectory = path.resolve(directory);
    
    return glob(pattern, {
      cwd: absoluteDirectory,
      ignore: [...CONFIG.IGNORE_PATTERNS, styleGuidePath],
    });
  }

  private async processFilesWithConcurrency(
    mdFiles: string[],
    styleGuide: string,
    options: ConversionOptions
  ): Promise<ConversionResult[]> {
    const limit = pLimit(options.concurrency);
    const promises = mdFiles.map(mdPath =>
      limit(() => this.processModule(mdPath, styleGuide, options))
    );
    return Promise.all(promises);
  }
}

// Environment checker
class EnvironmentChecker {
  static check(directory: string = process.cwd()): void {
    Logger.info('Environment Check');
    Logger.info(`Target directory: ${path.resolve(directory)}`);

    // Check API key
    try {
      Environment.validate();
      Logger.success('DEEPSEEK_API_KEY is set');
    } catch {
      Logger.error('DEEPSEEK_API_KEY is not set');
    }

    // Check Node version
    const nodeVersion = process.version;
    Logger.info(`Node.js version: ${nodeVersion}`);

    // Check style guide (async, fire and forget)
    const absoluteStyleGuidePath = path.resolve(directory, CONFIG.DEFAULTS.STYLE_GUIDE_PATH);
    FileUtils.readSafe(absoluteStyleGuidePath)
      .then(content => {
        if (content.trim()) {
          Logger.success(`Style guide found: ${absoluteStyleGuidePath}`);
        } else {
          Logger.warning(`Style guide not found: ${absoluteStyleGuidePath}`);
        }
      })
      .catch(() => {
        Logger.warning(`Style guide not found: ${absoluteStyleGuidePath}`);
      });
  }
}

// CLI setup
function createCLI(): Command {
  const program = new Command();

  program
    .name('adocify')
    .description('Convert Markdown files to AsciiDoc using AI-powered analysis')
    .version('1.0.0');

  program
    .command('convert')
    .description('Convert README.md files to README.adoc')
    .option(
      '-c, --concurrency <number>',
      'Number of concurrent conversions',
      (value: string) => {
        const num = parseInt(value, 10);
        if (isNaN(num) || num < 1) {
          throw new Error('Concurrency must be a positive number');
        }
        return num;
      },
      CONFIG.DEFAULTS.CONCURRENCY_LIMIT
    )
    .option('-v, --verbose', 'Enable verbose output', false)
    .option('-p, --pattern <pattern>', 'Glob pattern for markdown files', CONFIG.DEFAULTS.PATTERN)
    .option(
      '-s, --style-guide <path>',
      'Path to AsciiDoc style guide',
      CONFIG.DEFAULTS.STYLE_GUIDE_PATH
    )
    .option(
      '-d, --directory <path>',
      'Target directory to search for markdown files',
      process.cwd()
    )
    .action(async (options: ConversionOptions) => {
      try {
        Environment.validate();
        const converter = new MarkdownConverter();
        await converter.convertAll(options);
      } catch (error) {
        Logger.error(`Fatal error: ${(error as Error).message}`);
        process.exit(1);
      }
    });

  program
    .command('check')
    .description('Check environment and dependencies')
    .option(
      '-d, --directory <path>',
      'Target directory to check',
      process.cwd()
    )
    .action((options: { directory: string }) => {
      EnvironmentChecker.check(options.directory);
    });

  return program;
}

// Main execution
function main(): void {
  const program = createCLI();

  // Show help if no arguments provided
  if (process.argv.length === 2) {
    program.help();
    return;
  }

  program.parse();
}

// Handle uncaught errors
process.on('uncaughtException', error => {
  Logger.error(`Uncaught exception: ${error.message}`);
  process.exit(1);
});

process.on('unhandledRejection', reason => {
  Logger.error(`Unhandled rejection: ${reason}`);
  process.exit(1);
});

// Entry point
main();
