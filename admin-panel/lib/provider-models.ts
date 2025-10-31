/**
 * Provider Model Catalog
 * Maintains list of available models for each LLM provider
 */

export interface ProviderModel {
  value: string;
  label: string;
  description: string;
  contextWindow?: number;
  defaultInputPrice?: number;  // per 1M tokens
  defaultOutputPrice?: number; // per 1M tokens
}

export interface Provider {
  value: string;
  label: string;
  description: string;
  models: ProviderModel[];
}

export const PROVIDER_MODELS: Record<string, Provider> = {
  openai: {
    value: 'openai',
    label: 'OpenAI',
    description: 'GPT models from OpenAI',
    models: [
      {
        value: 'gpt-5',
        label: 'GPT-5',
        description: 'Latest flagship model, 400k context, reasoning & vision',
        contextWindow: 400000,
        defaultInputPrice: 1.25,
        defaultOutputPrice: 10.0,
      },
      {
        value: 'gpt-5-mini',
        label: 'GPT-5 Mini',
        description: 'Balanced model with reasoning, 400k context',
        contextWindow: 400000,
        defaultInputPrice: 0.25,
        defaultOutputPrice: 2.0,
      },
      {
        value: 'gpt-5-nano',
        label: 'GPT-5 Nano',
        description: 'Ultra-fast model with reasoning, 400k context',
        contextWindow: 400000,
        defaultInputPrice: 0.05,
        defaultOutputPrice: 0.4,
      },
      {
        value: 'gpt-4.1',
        label: 'GPT-4.1',
        description: 'Advanced model, 1M context with prompt caching',
        contextWindow: 1047576,
        defaultInputPrice: 2.0,
        defaultOutputPrice: 8.0,
      },
      {
        value: 'gpt-4.1-mini',
        label: 'GPT-4.1 Mini',
        description: 'Efficient model, 1M context with vision',
        contextWindow: 1047576,
        defaultInputPrice: 0.4,
        defaultOutputPrice: 1.6,
      },
      {
        value: 'gpt-4.1-nano',
        label: 'GPT-4.1 Nano',
        description: 'Ultra-fast, 1M context with vision',
        contextWindow: 1047576,
        defaultInputPrice: 0.1,
        defaultOutputPrice: 0.4,
      },
      {
        value: 'gpt-4o',
        label: 'GPT-4o',
        description: 'Omni model with vision & PDF, 128k context',
        contextWindow: 128000,
        defaultInputPrice: 2.5,
        defaultOutputPrice: 10.0,
      },
      {
        value: 'gpt-4o-mini',
        label: 'GPT-4o Mini',
        description: 'Fast omni model with vision, 128k context',
        contextWindow: 128000,
        defaultInputPrice: 0.15,
        defaultOutputPrice: 0.6,
      },
      {
        value: 'o3',
        label: 'o3',
        description: 'Advanced reasoning model, 200k context',
        contextWindow: 200000,
        defaultInputPrice: 1.0,
        defaultOutputPrice: 4.0,
      },
      {
        value: 'o4-mini',
        label: 'o4 Mini',
        description: 'Fast reasoning model, 200k context',
        contextWindow: 200000,
        defaultInputPrice: 0.3,
        defaultOutputPrice: 1.2,
      },
    ],
  },
  anthropic: {
    value: 'anthropic',
    label: 'Anthropic',
    description: 'Claude models from Anthropic',
    models: [
      {
        value: 'claude-opus-4-1',
        label: 'Claude Opus 4.1',
        description: 'Most capable Claude, 200k context, computer use',
        contextWindow: 200000,
        defaultInputPrice: 15.0,
        defaultOutputPrice: 75.0,
      },
      {
        value: 'claude-opus-4',
        label: 'Claude Opus 4',
        description: 'Most powerful Claude model, 200k context',
        contextWindow: 200000,
        defaultInputPrice: 15.0,
        defaultOutputPrice: 75.0,
      },
      {
        value: 'claude-sonnet-4-5',
        label: 'Claude Sonnet 4.5',
        description: 'Latest Sonnet, 200k context, PDF & computer use',
        contextWindow: 200000,
        defaultInputPrice: 3.0,
        defaultOutputPrice: 15.0,
      },
      {
        value: 'claude-sonnet-4',
        label: 'Claude Sonnet 4',
        description: 'Balanced Claude, 200k context, 64k output',
        contextWindow: 200000,
        defaultInputPrice: 3.0,
        defaultOutputPrice: 15.0,
      },
      {
        value: 'claude-sonnet-3-7',
        label: 'Claude Sonnet 3.7',
        description: 'Previous Sonnet, 200k context, 64k output',
        contextWindow: 200000,
        defaultInputPrice: 3.0,
        defaultOutputPrice: 15.0,
      },
      {
        value: 'claude-haiku-4-5',
        label: 'Claude Haiku 4.5',
        description: 'Fast & capable, 200k context, computer use',
        contextWindow: 200000,
        defaultInputPrice: 1.0,
        defaultOutputPrice: 5.0,
      },
      {
        value: 'claude-haiku-3-5',
        label: 'Claude Haiku 3.5',
        description: 'Fast Claude, 200k context, vision',
        contextWindow: 200000,
        defaultInputPrice: 0.8,
        defaultOutputPrice: 4.0,
      },
      {
        value: 'claude-haiku-3',
        label: 'Claude Haiku 3',
        description: 'Fastest Claude model, 200k context',
        contextWindow: 200000,
        defaultInputPrice: 0.25,
        defaultOutputPrice: 1.25,
      },
    ],
  },
  gemini: {
    value: 'gemini',
    label: 'Google Gemini',
    description: 'Gemini models from Google',
    models: [
      {
        value: 'gemini-2.5-pro',
        label: 'Gemini 2.5 Pro',
        description: 'Most advanced, 2M context, reasoning & audio',
        contextWindow: 2097152,
        defaultInputPrice: 1.25,
        defaultOutputPrice: 5.0,
      },
      {
        value: 'gemini-2.5-flash',
        label: 'Gemini 2.5 Flash',
        description: 'Ultra-fast, 1M context, reasoning & audio',
        contextWindow: 1048576,
        defaultInputPrice: 0.075,
        defaultOutputPrice: 0.3,
      },
      {
        value: 'gemini-2.5-flash-lite',
        label: 'Gemini 2.5 Flash Lite',
        description: 'Lightweight, 1M context, vision',
        contextWindow: 1048576,
        defaultInputPrice: 0.02,
        defaultOutputPrice: 0.08,
      },
      {
        value: 'gemini-2.0-pro',
        label: 'Gemini 2.0 Pro (Experimental)',
        description: 'Latest experimental, 2M context, vision',
        contextWindow: 2097152,
        defaultInputPrice: 2.5,
        defaultOutputPrice: 10.0,
      },
      {
        value: 'gemini-2.0-flash',
        label: 'Gemini 2.0 Flash',
        description: 'Fast 2.0 model, 1M context, audio',
        contextWindow: 1048576,
        defaultInputPrice: 0.1,
        defaultOutputPrice: 0.4,
      },
      {
        value: 'gemini-2.0-flash-lite',
        label: 'Gemini 2.0 Flash Lite',
        description: 'Lightweight 2.0, 1M context, vision',
        contextWindow: 1048576,
        defaultInputPrice: 0.04,
        defaultOutputPrice: 0.16,
      },
      {
        value: 'gemini-1.5-pro',
        label: 'Gemini 1.5 Pro',
        description: 'Advanced 1.5, 2M context, vision',
        contextWindow: 2097152,
        defaultInputPrice: 1.25,
        defaultOutputPrice: 5.0,
      },
      {
        value: 'gemini-1.5-flash',
        label: 'Gemini 1.5 Flash',
        description: 'Fast 1.5, 1M context, vision',
        contextWindow: 1048576,
        defaultInputPrice: 0.075,
        defaultOutputPrice: 0.3,
      },
    ],
  },
  fireworks: {
    value: 'fireworks',
    label: 'Fireworks AI',
    description: 'Open source models via Fireworks',
    models: [
      {
        value: 'llama-v3p3-70b-instruct',
        label: 'Llama 3.3 70B Instruct',
        description: 'Latest Llama 3.3, 131k context, function calling',
        contextWindow: 131072,
        defaultInputPrice: 0.9,
        defaultOutputPrice: 0.9,
      },
      {
        value: 'llama-v3p1-405b-instruct',
        label: 'Llama 3.1 405B Instruct',
        description: 'Largest Llama, 131k context, function calling',
        contextWindow: 131072,
        defaultInputPrice: 0.9,
        defaultOutputPrice: 0.9,
      },
      {
        value: 'llama-v3p1-70b-instruct',
        label: 'Llama 3.1 70B Instruct',
        description: 'Meta Llama 3.1, 131k context, function calling',
        contextWindow: 131072,
        defaultInputPrice: 0.9,
        defaultOutputPrice: 0.9,
      },
      {
        value: 'llama-v3p1-8b-instruct',
        label: 'Llama 3.1 8B Instruct',
        description: 'Fast Llama, 131k context, function calling',
        contextWindow: 131072,
        defaultInputPrice: 0.2,
        defaultOutputPrice: 0.2,
      },
      {
        value: 'deepseek-r1',
        label: 'DeepSeek R1',
        description: 'Reasoning model, 64k context',
        contextWindow: 64000,
        defaultInputPrice: 0.9,
        defaultOutputPrice: 0.9,
      },
      {
        value: 'qwen2p5-72b-instruct',
        label: 'Qwen 2.5 72B Instruct',
        description: 'Qwen 2.5, 131k context, function calling',
        contextWindow: 131072,
        defaultInputPrice: 0.9,
        defaultOutputPrice: 0.9,
      },
      {
        value: 'mixtral-8x22b-instruct',
        label: 'Mixtral 8x22B Instruct',
        description: 'Large Mixtral MoE, 65k context, function calling',
        contextWindow: 65536,
        defaultInputPrice: 1.2,
        defaultOutputPrice: 1.2,
      },
      {
        value: 'mixtral-8x7b-instruct',
        label: 'Mixtral 8x7B Instruct',
        description: 'Efficient MoE, 32k context, function calling',
        contextWindow: 32768,
        defaultInputPrice: 0.5,
        defaultOutputPrice: 0.5,
      },
      {
        value: 'phi-3-vision-128k-instruct',
        label: 'Phi-3 Vision 128k',
        description: 'Small vision model, 128k context',
        contextWindow: 128000,
        defaultInputPrice: 0.2,
        defaultOutputPrice: 0.2,
      },
      {
        value: 'firellava-13b',
        label: 'FireLLaVA 13B',
        description: 'Vision model, 4k context',
        contextWindow: 4096,
        defaultInputPrice: 0.2,
        defaultOutputPrice: 0.2,
      },
    ],
  },
};

export const PROVIDERS: Provider[] = Object.values(PROVIDER_MODELS);

/**
 * Get models for a specific provider
 */
export function getModelsForProvider(provider: string): ProviderModel[] {
  return PROVIDER_MODELS[provider]?.models || [];
}

/**
 * Get provider information
 */
export function getProvider(provider: string): Provider | null {
  return PROVIDER_MODELS[provider] || null;
}

/**
 * Get model information
 */
export function getModel(provider: string, modelValue: string): ProviderModel | null {
  const providerInfo = PROVIDER_MODELS[provider];
  if (!providerInfo) return null;

  return providerInfo.models.find(m => m.value === modelValue) || null;
}
