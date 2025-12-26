# Project Plan: Model-Backend Mapping Conceptual Change

**Date:** 2025-12-25 22:48:06
**Estimated Duration:** 3-4 hours
**Complexity:** Medium
**Status:** Draft

## Objective
Implement a conceptual change in how models are configured and managed. Currently, models are simple named entities. The new concept introduces a clear separation between:

1. **Model**: What clients see and interact with (exposed interface)
2. **Backend**: The actual model implementation at a provider (ollama, gemini, anthropic, openai, etc.)

This change enables flexible mapping between user-facing model names and provider-specific backend configurations, supporting features like model aliases, provider failover, and multi-provider support.

## Requirements
- [ ] Document the conceptual change from simple models to model-backend mapping
- [ ] Design new configuration structure supporting model-to-backend relationships
- [ ] Create backward-compatible configuration parsing
- [ ] Implement backend provider abstraction layer
- [ ] Add model resolution and routing logic
- [ ] Update any existing model usage to work with new system
- [ ] Add configuration validation for model-backend mappings
- [ ] Create examples and documentation for the new configuration format

## Current State Analysis
The project currently has no model configuration system. This conceptual change establishes the foundation for a flexible, multi-provider model management system.

## Conceptual Change Details

### Before (Simple Model Concept)
```
models:
  - name: "gpt-4"
  - name: "claude-3"
```

### After (Model + Backend Concept)
```
models:
  gpt-4:
    backend: "openai/gpt-4"
    description: "GPT-4 from OpenAI"
    capabilities: ["chat", "completion"]

  claude-3:
    backend: "anthropic/claude-3-sonnet-20240229"
    description: "Claude 3 from Anthropic"
    capabilities: ["chat", "completion"]

backends:
  openai:
    provider: "openai"
    api_key: "${OPENAI_API_KEY}"
    base_url: "https://api.openai.com/v1"

  anthropic:
    provider: "anthropic"
    api_key: "${ANTHROPIC_API_KEY}"
    base_url: "https://api.anthropic.com"
```

## Implementation Steps
1. **Create conceptual change documentation**
   - Files to create: `doc/model-backend-concept.md`
   - Files to modify: None
   - Dependencies: None
   - Estimated time: 30 minutes
   - Status: [ ] Not Started / [ ] In Progress / [x] Completed

2. **Design configuration schema**
   - Files to create: `src/slack_agent/model_config.py`
   - Files to modify: None
   - Dependencies: pydantic for validation
   - Estimated time: 45 minutes
   - Status: [ ] Not Started / [ ] In Progress / [ ] Completed

3. **Implement backend provider abstraction**
   - Files to create: `src/slack_agent/backends/`
   - Files to modify: None
   - Dependencies: httpx for API calls
   - Estimated time: 1 hour
   - Status: [ ] Not Started / [ ] In Progress / [ ] Completed

4. **Create model resolver and router**
   - Files to create: `src/slack_agent/model_resolver.py`
   - Files to modify: None
   - Dependencies: Backend abstraction
   - Estimated time: 45 minutes
   - Status: [ ] Not Started / [ ] In Progress / [ ] Completed

5. **Update configuration parsing**
   - Files to create: `src/slack_agent/config_models.py`
   - Files to modify: Existing config files
   - Dependencies: pydantic models
   - Estimated time: 45 minutes
   - Status: [ ] Not Started / [ ] In Progress / [ ] Completed

6. **Add configuration validation**
   - Files to create: `src/slack_agent/config_validator.py`
   - Files to modify: None
   - Dependencies: Configuration schema
   - Estimated time: 30 minutes
   - Status: [ ] Not Started / [ ] In Progress / [ ] Completed

7. **Create configuration examples and docs**
   - Files to create: `examples/model_config_example.yaml`
   - Files to modify: `README.md` (add model config section)
   - Dependencies: None
   - Estimated time: 30 minutes
   - Status: [ ] Not Started / [ ] In Progress / [x] Completed

## Configuration Structure Design

### Model Configuration Schema
```yaml
# Top-level configuration structure
models:     # What clients see and interact with
  [model_name]:
    backend: "[provider]/[backend_model_name]"
    description: "Human-readable description"
    capabilities: ["chat", "completion", "embedding"]
    parameters:
      temperature: 0.7
      max_tokens: 4096
    aliases: ["alias1", "alias2"]  # Alternative names

backends:   # Provider-specific configurations
  [provider_name]:
    provider: "[provider_type]"  # openai, anthropic, ollama, etc.
    api_key: "${ENV_VAR}"
    base_url: "https://api.provider.com"
    models:
      [backend_model_name]:
        context_window: 4096
        pricing:
          input: 0.0015
          output: 0.002
    rate_limits:
      requests_per_minute: 60
      tokens_per_minute: 100000

# Global settings
model_defaults:
  temperature: 0.7
  max_tokens: 2048

fallback_providers:  # For failover scenarios
  - provider: "openai"
  - provider: "anthropic"
```

### Provider Types Supported
- **openai**: GPT models, DALL-E, Whisper
- **anthropic**: Claude models
- **google**: Gemini models
- **ollama**: Local LLM models
- **together**: Together AI models
- **huggingface**: Hugging Face models
- **custom**: Generic API-compatible providers

## Success Criteria
- [ ] Conceptual documentation clearly explains model vs backend distinction
- [ ] Configuration schema supports flexible model-backend mapping
- [ ] Backward compatibility maintained for simple configurations
- [ ] Provider abstraction allows easy addition of new backends
- [ ] Model resolution correctly maps user requests to backend implementations
- [ ] Configuration validation catches common errors
- [ ] Example configurations demonstrate all major use cases

## Testing Strategy
- [ ] Unit tests for configuration parsing and validation
- [ ] Unit tests for model resolution logic
- [ ] Integration tests for backend provider abstraction
- [ ] Mock tests for provider API interactions
- [ ] Configuration file validation tests
- [ ] Error handling tests for invalid configurations

## Risk Assessment
- **Medium Risk:** Configuration complexity increase
  - **Mitigation:** Provide clear examples and validation with helpful error messages
- **Low Risk:** Breaking changes for existing simple model configs
  - **Mitigation:** Implement backward-compatible parsing
- **Medium Risk:** Provider abstraction complexity
  - **Mitigation:** Start with core providers (OpenAI, Anthropic, Ollama) and expand incrementally

## Dependencies
- [ ] pydantic >= 2.0.0 (for configuration validation)
- [ ] httpx >= 0.25.0 (for backend API calls)
- [ ] python-dotenv >= 1.0.0 (for environment variable expansion)
- [ ] pyyaml >= 6.0 (for YAML configuration parsing)

## Notes
This conceptual change establishes the foundation for a robust, multi-provider model management system. The separation of "model" (user interface) from "backend" (provider implementation) enables:

1. **Provider Agnosticism**: Easy switching between providers
2. **Model Aliases**: Multiple names for the same model
3. **Failover Support**: Automatic fallback to alternative providers
4. **Cost Optimization**: Route to cheapest/most available provider
5. **Feature Flags**: Enable/disable capabilities per model
6. **Unified Interface**: Consistent API regardless of backend

The implementation should be designed to be extensible, allowing new providers to be added with minimal code changes.