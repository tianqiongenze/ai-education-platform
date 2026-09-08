import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';

import { ISettingRegistry } from '@jupyterlab/settingregistry';

import {
  ICompletionProviderManager,
  IInlineCompletionProvider,
  InlineCompletionTriggerKind,
  IInlineCompletionContext,
  IInlineCompletion
} from '@jupyterlab/completer';

/**
 * AI inline completion provider using the FIM service backend.
 * Cache-first, with ollama fallback (via the server-side handler).
 */
const PLUGIN_ID = 'jupyter-inline-completion:plugin';

const provider: JupyterFrontEndPlugin<void> = {
  id: PLUGIN_ID,
  autoStart: true,
  requires: [ICompletionProviderManager],
  optional: [ISettingRegistry],
  activate: async (
    app: JupyterFrontEnd,
    manager: ICompletionProviderManager,
    settings: ISettingRegistry | null
  ) => {
    console.log('JupyterLab inline completion extension is activated!');

    let enabled = true;
    let endpoint = '/inline-completion/v1/completion';
    let debounceMs = 600;
    let maxTokens = 32;

    if (settings) {
      const setting = await settings.load(PLUGIN_ID);
      const updateSettings = () => {
        enabled = setting.get('enabled').composite as boolean;
        endpoint = setting.get('endpoint').composite as string;
        debounceMs = setting.get('debounceMs').composite as number;
        maxTokens = setting.get('maxTokens').composite as number;
      };
      updateSettings();
      setting.changed.connect(updateSettings);
    }

    const inlineProvider: IInlineCompletionProvider = {
      identifier: 'ai-inline-completion',
      name: 'AI Inline Completion',
      async fetch(
        request: any,
        context: IInlineCompletionContext,
        triggerKind: InlineCompletionTriggerKind
      ): Promise<IInlineCompletion | null> {
        if (!enabled) {
          return null;
        }

        // Build FIM payload
        const prefix = request.text ?? '';
        const suffix = request.suffix ?? '';
        const language = (context as any)?.mimeType ?? 'python';
        const filename = (context as any)?.path ?? 'untitled.py';

        // Debounce: wait before sending request
        await new Promise(resolve => setTimeout(resolve, debounceMs));

        // Check if the user is still typing after debounce
        if (triggerKind === InlineCompletionTriggerKind.Automatic && prefix.trim().length < 3) {
          return null;
        }

        try {
          const response = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              prefix: prefix.slice(-1024),  // last 1KB of prefix
              suffix: suffix.slice(0, 512),  // first 512B of suffix
              language: language,
              filename: filename,
              max_tokens: maxTokens
            })
          });

          if (!response.ok) {
            console.warn('Inline completion request failed:', response.status);
            return null;
          }

          const data = await response.json();

          if (data.suggestion && data.suggestion.trim()) {
            return {
              suggestions: [data.suggestion]
            } as any;
          }
        } catch (err) {
          console.warn('Inline completion error:', err);
        }

        return null;
      }
    };

    // Register with the completion manager
    manager.registerInlineProvider(inlineProvider);
    console.log('AI inline completion provider registered');
  }
};

export default provider;
