/**
 * Tests for Provider Models Catalog
 *
 * Tests the provider model catalog used in the admin panel for model selection.
 */

import { describe, it, expect } from '@jest/globals';
import {
  PROVIDER_MODELS,
  PROVIDERS,
  getModelsForProvider,
  getProvider,
  getModel,
  type Provider,
  type ProviderModel
} from './provider-models';

describe('Provider Models Catalog', () => {
  describe('PROVIDER_MODELS constant', () => {
    it('should have all four providers', () => {
      expect(PROVIDER_MODELS).toHaveProperty('openai');
      expect(PROVIDER_MODELS).toHaveProperty('anthropic');
      expect(PROVIDER_MODELS).toHaveProperty('gemini');
      expect(PROVIDER_MODELS).toHaveProperty('fireworks');
    });

    it('should have provider metadata', () => {
      const openai = PROVIDER_MODELS.openai;
      expect(openai.value).toBe('openai');
      expect(openai.label).toBe('OpenAI');
      expect(openai.description).toBeTruthy();
      expect(Array.isArray(openai.models)).toBe(true);
    });
  });

  describe('PROVIDERS array', () => {
    it('should contain all providers as array', () => {
      expect(Array.isArray(PROVIDERS)).toBe(true);
      expect(PROVIDERS.length).toBe(4);
    });

    it('should contain correct provider values', () => {
      const providerValues = PROVIDERS.map(p => p.value);
      expect(providerValues).toContain('openai');
      expect(providerValues).toContain('anthropic');
      expect(providerValues).toContain('gemini');
      expect(providerValues).toContain('fireworks');
    });
  });

  describe('OpenAI Models', () => {
    it('should have latest GPT-5 models', () => {
      const models = PROVIDER_MODELS.openai.models;
      const modelValues = models.map(m => m.value);

      expect(modelValues).toContain('gpt-5');
      expect(modelValues).toContain('gpt-5-mini');
      expect(modelValues).toContain('gpt-5-nano');
    });

    it('should have GPT-4.1 models', () => {
      const models = PROVIDER_MODELS.openai.models;
      const modelValues = models.map(m => m.value);

      expect(modelValues).toContain('gpt-4.1');
      expect(modelValues).toContain('gpt-4.1-mini');
      expect(modelValues).toContain('gpt-4.1-nano');
    });

    it('should have GPT-4o models', () => {
      const models = PROVIDER_MODELS.openai.models;
      const modelValues = models.map(m => m.value);

      expect(modelValues).toContain('gpt-4o');
      expect(modelValues).toContain('gpt-4o-mini');
    });

    it('should have reasoning models', () => {
      const models = PROVIDER_MODELS.openai.models;
      const modelValues = models.map(m => m.value);

      expect(modelValues).toContain('o3');
      expect(modelValues).toContain('o4-mini');
    });

    it('should have accurate pricing for GPT-4o', () => {
      const gpt4o = PROVIDER_MODELS.openai.models.find(m => m.value === 'gpt-4o');
      expect(gpt4o).toBeDefined();
      expect(gpt4o?.defaultInputPrice).toBe(2.5);
      expect(gpt4o?.defaultOutputPrice).toBe(10.0);
    });

    it('should have context window information', () => {
      const gpt5 = PROVIDER_MODELS.openai.models.find(m => m.value === 'gpt-5');
      expect(gpt5?.contextWindow).toBe(400000);
    });
  });

  describe('Anthropic Models', () => {
    it('should have latest Claude Opus 4 models', () => {
      const models = PROVIDER_MODELS.anthropic.models;
      const modelValues = models.map(m => m.value);

      expect(modelValues).toContain('claude-opus-4-1');
      expect(modelValues).toContain('claude-opus-4');
    });

    it('should have Claude Sonnet 4 models', () => {
      const models = PROVIDER_MODELS.anthropic.models;
      const modelValues = models.map(m => m.value);

      expect(modelValues).toContain('claude-sonnet-4-5');
      expect(modelValues).toContain('claude-sonnet-4');
      expect(modelValues).toContain('claude-sonnet-3-7');
    });

    it('should have Claude Haiku models', () => {
      const models = PROVIDER_MODELS.anthropic.models;
      const modelValues = models.map(m => m.value);

      expect(modelValues).toContain('claude-haiku-4-5');
      expect(modelValues).toContain('claude-haiku-3-5');
      expect(modelValues).toContain('claude-haiku-3');
    });

    it('should have accurate pricing for Claude Sonnet 4.5', () => {
      const sonnet45 = PROVIDER_MODELS.anthropic.models.find(
        m => m.value === 'claude-sonnet-4-5'
      );
      expect(sonnet45).toBeDefined();
      expect(sonnet45?.defaultInputPrice).toBe(3.0);
      expect(sonnet45?.defaultOutputPrice).toBe(15.0);
    });
  });

  describe('Google Gemini Models', () => {
    it('should have latest Gemini 2.5 models', () => {
      const models = PROVIDER_MODELS.gemini.models;
      const modelValues = models.map(m => m.value);

      expect(modelValues).toContain('gemini-2.5-pro');
      expect(modelValues).toContain('gemini-2.5-flash');
      expect(modelValues).toContain('gemini-2.5-flash-lite');
    });

    it('should have Gemini 2.0 models', () => {
      const models = PROVIDER_MODELS.gemini.models;
      const modelValues = models.map(m => m.value);

      expect(modelValues).toContain('gemini-2.0-pro');
      expect(modelValues).toContain('gemini-2.0-flash');
      expect(modelValues).toContain('gemini-2.0-flash-lite');
    });

    it('should have Gemini 1.5 models', () => {
      const models = PROVIDER_MODELS.gemini.models;
      const modelValues = models.map(m => m.value);

      expect(modelValues).toContain('gemini-1.5-pro');
      expect(modelValues).toContain('gemini-1.5-flash');
    });

    it('should have accurate pricing for Gemini 2.5 Pro', () => {
      const gemini25pro = PROVIDER_MODELS.gemini.models.find(
        m => m.value === 'gemini-2.5-pro'
      );
      expect(gemini25pro).toBeDefined();
      expect(gemini25pro?.defaultInputPrice).toBe(1.25);
      expect(gemini25pro?.defaultOutputPrice).toBe(5.0);
    });

    it('should have large context windows', () => {
      const gemini25pro = PROVIDER_MODELS.gemini.models.find(
        m => m.value === 'gemini-2.5-pro'
      );
      expect(gemini25pro?.contextWindow).toBe(2097152); // 2M tokens
    });
  });

  describe('Fireworks AI Models', () => {
    it('should have Llama models', () => {
      const models = PROVIDER_MODELS.fireworks.models;
      const modelValues = models.map(m => m.value);

      expect(modelValues).toContain('llama-v3p3-70b-instruct');
      expect(modelValues).toContain('llama-v3p1-405b-instruct');
      expect(modelValues).toContain('llama-v3p1-70b-instruct');
      expect(modelValues).toContain('llama-v3p1-8b-instruct');
    });

    it('should have DeepSeek R1 reasoning model', () => {
      const models = PROVIDER_MODELS.fireworks.models;
      const modelValues = models.map(m => m.value);

      expect(modelValues).toContain('deepseek-r1');

      const deepseek = models.find(m => m.value === 'deepseek-r1');
      expect(deepseek?.description).toContain('Reasoning');
    });

    it('should have Qwen model', () => {
      const models = PROVIDER_MODELS.fireworks.models;
      const modelValues = models.map(m => m.value);

      expect(modelValues).toContain('qwen2p5-72b-instruct');
    });

    it('should have Mixtral models', () => {
      const models = PROVIDER_MODELS.fireworks.models;
      const modelValues = models.map(m => m.value);

      expect(modelValues).toContain('mixtral-8x22b-instruct');
      expect(modelValues).toContain('mixtral-8x7b-instruct');
    });

    it('should have vision models', () => {
      const models = PROVIDER_MODELS.fireworks.models;
      const modelValues = models.map(m => m.value);

      expect(modelValues).toContain('phi-3-vision-128k-instruct');
      expect(modelValues).toContain('firellava-13b');
    });

    it('should have accurate pricing', () => {
      const llama33 = PROVIDER_MODELS.fireworks.models.find(
        m => m.value === 'llama-v3p3-70b-instruct'
      );
      expect(llama33).toBeDefined();
      expect(llama33?.defaultInputPrice).toBe(0.9);
      expect(llama33?.defaultOutputPrice).toBe(0.9);
    });
  });

  describe('getModelsForProvider function', () => {
    it('should return models for valid provider', () => {
      const openaiModels = getModelsForProvider('openai');
      expect(Array.isArray(openaiModels)).toBe(true);
      expect(openaiModels.length).toBeGreaterThan(0);
    });

    it('should return empty array for invalid provider', () => {
      const invalidModels = getModelsForProvider('invalid_provider');
      expect(Array.isArray(invalidModels)).toBe(true);
      expect(invalidModels.length).toBe(0);
    });

    it('should return different models for different providers', () => {
      const openaiModels = getModelsForProvider('openai');
      const anthropicModels = getModelsForProvider('anthropic');

      expect(openaiModels).not.toEqual(anthropicModels);
    });
  });

  describe('getProvider function', () => {
    it('should return provider info for valid provider', () => {
      const openai = getProvider('openai');
      expect(openai).toBeTruthy();
      expect(openai?.value).toBe('openai');
      expect(openai?.label).toBe('OpenAI');
    });

    it('should return null for invalid provider', () => {
      const invalid = getProvider('invalid_provider');
      expect(invalid).toBeNull();
    });
  });

  describe('getModel function', () => {
    it('should return model info for valid provider and model', () => {
      const gpt5 = getModel('openai', 'gpt-5');
      expect(gpt5).toBeTruthy();
      expect(gpt5?.value).toBe('gpt-5');
      expect(gpt5?.label).toBe('GPT-5');
    });

    it('should return null for invalid provider', () => {
      const model = getModel('invalid_provider', 'gpt-5');
      expect(model).toBeNull();
    });

    it('should return null for invalid model', () => {
      const model = getModel('openai', 'nonexistent-model');
      expect(model).toBeNull();
    });

    it('should return null for model from wrong provider', () => {
      const model = getModel('openai', 'claude-sonnet-4-5');
      expect(model).toBeNull();
    });
  });

  describe('Model metadata completeness', () => {
    it('all models should have required fields', () => {
      Object.values(PROVIDER_MODELS).forEach(provider => {
        provider.models.forEach(model => {
          expect(model.value).toBeTruthy();
          expect(model.label).toBeTruthy();
          expect(model.description).toBeTruthy();
        });
      });
    });

    it('all models should have pricing information', () => {
      Object.values(PROVIDER_MODELS).forEach(provider => {
        provider.models.forEach(model => {
          expect(typeof model.defaultInputPrice).toBe('number');
          expect(typeof model.defaultOutputPrice).toBe('number');
          expect(model.defaultInputPrice).toBeGreaterThan(0);
          expect(model.defaultOutputPrice).toBeGreaterThan(0);
        });
      });
    });

    it('all models should have context window information', () => {
      Object.values(PROVIDER_MODELS).forEach(provider => {
        provider.models.forEach(model => {
          expect(typeof model.contextWindow).toBe('number');
          expect(model.contextWindow).toBeGreaterThan(0);
        });
      });
    });
  });

  describe('Pricing accuracy from llm_pricing_current.json', () => {
    it('should match actual provider pricing for key models', () => {
      // GPT-5: $1.25 input, $10.00 output per 1M tokens
      const gpt5 = getModel('openai', 'gpt-5');
      expect(gpt5?.defaultInputPrice).toBe(1.25);
      expect(gpt5?.defaultOutputPrice).toBe(10.0);

      // Claude Opus 4.1: $15.00 input, $75.00 output per 1M tokens
      const opus41 = getModel('anthropic', 'claude-opus-4-1');
      expect(opus41?.defaultInputPrice).toBe(15.0);
      expect(opus41?.defaultOutputPrice).toBe(75.0);

      // Gemini 2.5 Flash: $0.075 input, $0.30 output per 1M tokens
      const gemini25flash = getModel('gemini', 'gemini-2.5-flash');
      expect(gemini25flash?.defaultInputPrice).toBe(0.075);
      expect(gemini25flash?.defaultOutputPrice).toBe(0.3);

      // DeepSeek R1: $0.90 input/output per 1M tokens
      const deepseek = getModel('fireworks', 'deepseek-r1');
      expect(deepseek?.defaultInputPrice).toBe(0.9);
      expect(deepseek?.defaultOutputPrice).toBe(0.9);
    });
  });
});
