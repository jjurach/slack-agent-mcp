# Model-Backend Mapping: Conceptual Change

## Overview

This document outlines a fundamental conceptual change in how models are configured and managed within the system. The change introduces a clear separation between what clients interact with (models) and how those models are implemented (backends).

## Current Concept (Simple Models)

In the current conceptual model, a "model" is simply a named entity that represents an AI model available for use:

```
Models Available:
- GPT-4
- Claude-3
- Llama-3
- Gemini-1.5
```

Each model is treated as a monolithic entity with no distinction between:
- What users see and select
- How the model is actually implemented
- Which provider hosts the model

## New Concept (Models + Backends)

The new concept introduces a clear separation:

### Model (User Interface)
A **model** is what clients see and interact with. It represents the exposed interface and user experience:

- **Name**: Human-friendly identifier (e.g., "gpt-4", "creative-writer")
- **Description**: What this model does and its capabilities
- **Capabilities**: What the model can do (chat, completion, embedding, etc.)
- **Parameters**: Default settings (temperature, max_tokens, etc.)
- **Aliases**: Alternative names for the same model

### Backend (Implementation)
A **backend** is the actual implementation at a provider. It represents the technical details:

- **Provider**: The service hosting the model (OpenAI, Anthropic, Ollama, etc.)
- **Model ID**: The provider-specific identifier
- **API Configuration**: Keys, endpoints, authentication
- **Technical Specs**: Context window, pricing, rate limits
- **Capabilities**: What the backend actually supports

## Why This Change Matters

### 1. Provider Agnosticism
Users can work with familiar model names while the system routes to different providers based on:
- Cost optimization
- Availability
- Performance requirements
- Geographic preferences

### 2. Model Aliases
Single backend models can be exposed under multiple names:
```
Model: "creative-writer" → Backend: "openai/gpt-4"
Model: "code-assistant" → Backend: "anthropic/claude-3-sonnet"
Model: "fast-chat" → Backend: "ollama/llama3.2:3b"
```

### 3. Failover and Redundancy
If one provider is down, requests can automatically route to alternatives:
```
Primary: "openai/gpt-4"
Fallback: "anthropic/claude-3-sonnet"
Fallback: "google/gemini-pro"
```

### 4. Cost Optimization
Route to the most cost-effective provider for specific use cases:
```
High-quality writing → "anthropic/claude-3-opus"
Fast responses → "ollama/llama3.2:3b"
Budget tasks → "openai/gpt-3.5-turbo"
```

### 5. Feature Flags
Enable/disable capabilities per model independently of the backend:
```
Model: "safe-chat" (filtered) → Backend: "openai/gpt-4" (unfiltered)
Model: "creative-unlimited" → Backend: "anthropic/claude-3" (same backend, different policies)
```

## Configuration Structure

### Before (Simple)
```yaml
models:
  - gpt-4
  - claude-3
  - llama-3

providers:
  openai:
    api_key: "${OPENAI_API_KEY}"
  anthropic:
    api_key: "${ANTHROPIC_API_KEY}"
```

### After (Model + Backend)
```yaml
models:
  gpt-4:
    backend: "openai/gpt-4"
    description: "GPT-4 from OpenAI"
    capabilities: ["chat", "completion"]
    parameters:
      temperature: 0.7
      max_tokens: 4096

  creative-writer:
    backend: "anthropic/claude-3-sonnet"
    description: "Creative writing assistant"
    capabilities: ["chat", "completion"]
    parameters:
      temperature: 0.9
      max_tokens: 8192

  fast-responder:
    backend: "ollama/llama3.2:3b"
    description: "Fast local responses"
    capabilities: ["chat"]
    parameters:
      temperature: 0.3

backends:
  openai:
    provider: "openai"
    api_key: "${OPENAI_API_KEY}"
    base_url: "https://api.openai.com/v1"
    models:
      gpt-4:
        context_window: 8192
        pricing:
          input: 0.03
          output: 0.06

  anthropic:
    provider: "anthropic"
    api_key: "${ANTHROPIC_API_KEY}"
    base_url: "https://api.anthropic.com"
    models:
      claude-3-sonnet:
        context_window: 200000
        pricing:
          input: 0.015
          output: 0.075

  ollama:
    provider: "ollama"
    base_url: "http://localhost:11434"
    models:
      llama3.2:3b:
        context_window: 4096
        pricing:
          input: 0
          output: 0
```

## Implementation Benefits

### For Users
- **Consistency**: Same interface regardless of backend provider
- **Flexibility**: Choose models by capability rather than provider
- **Reliability**: Automatic failover to alternative providers
- **Cost Control**: Transparent pricing and optimization

### For Developers
- **Extensibility**: Easy addition of new providers
- **Maintainability**: Clear separation of concerns
- **Testability**: Mock backends for testing
- **Monitoring**: Track usage and performance per model/backend

### For System Administrators
- **Load Balancing**: Distribute load across multiple providers
- **Cost Management**: Optimize spending across providers
- **Compliance**: Route sensitive requests to approved providers
- **Monitoring**: Track performance and reliability per backend

## Migration Path

### Phase 1: Configuration Schema
- Implement new configuration structure
- Maintain backward compatibility
- Add validation and documentation

### Phase 2: Core Abstraction
- Create backend provider interfaces
- Implement model resolution logic
- Add configuration parsing

### Phase 3: Provider Support
- Implement core providers (OpenAI, Anthropic, Ollama)
- Add comprehensive testing
- Create provider documentation

### Phase 4: Advanced Features
- Implement failover logic
- Add cost optimization
- Create monitoring and analytics

## Backward Compatibility

The new system maintains backward compatibility by:
- Accepting simple model lists and auto-generating backend configurations
- Providing migration tools to convert old configurations
- Supporting both old and new configuration formats during transition

## Examples

### Basic Mapping
```yaml
models:
  gpt-4: "openai/gpt-4"  # Simple string mapping
  claude: "anthropic/claude-3-sonnet"

backends:
  openai:
    provider: "openai"
    api_key: "${OPENAI_API_KEY}"
```

### Advanced Configuration
```yaml
models:
  premium-writer:
    backend: "anthropic/claude-3-opus"
    description: "High-quality creative writing"
    capabilities: ["chat", "completion", "editing"]
    parameters:
      temperature: 0.8
      max_tokens: 4096
    aliases: ["writer", "author"]

  budget-chat:
    backend: "openai/gpt-3.5-turbo"
    description: "Cost-effective conversations"
    capabilities: ["chat"]
    parameters:
      temperature: 0.7
      max_tokens: 2048

backends:
  anthropic:
    provider: "anthropic"
    api_key: "${ANTHROPIC_API_KEY}"
    rate_limits:
      requests_per_minute: 50

  openai:
    provider: "openai"
    api_key: "${OPENAI_API_KEY}"
    rate_limits:
      requests_per_minute: 3500
```

This conceptual change provides a solid foundation for a flexible, scalable, and user-friendly model management system.