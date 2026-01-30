# Future Enhancements (Phase 2 & Beyond)

This document outlines features, improvements, and architectural changes deferred from Phase 1 for future implementation. Each section provides design considerations, trade-offs, and implementation guidance.

---

## 1. Credential Encryption at Rest

### Context

Currently, `credentials.json` and `token.json` are stored as plain text JSON files in `~/.config/google-personal-mcp/profiles/{profile}/`.

**Security Risk:** If user's home directory or config directory is compromised, credentials are exposed.

### Approaches

#### Approach A: OS Keyring (Most Secure)

Uses the operating system's native secret storage:
- **Linux:** `secretstorage` (via D-Bus)
- **macOS:** Keychain
- **Windows:** Windows Credential Manager

**Library:** `keyring` Python package

**Pros:**
- Most secure (OS-managed, encrypted at rest)
- No additional encryption keys to manage
- User can use system key manager (e.g., unlock keyring on login)
- Per-profile isolation through keyring item names

**Cons:**
- OS-specific setup required
- D-Bus dependency on Linux (not available in headless/container)
- More complex to test
- Fallback needed for environments without keyring (CI/CD, containers, headless servers)

**Implementation Outline:**

```python
import keyring

class KeyringCredentialStore:
    def __init__(self, profile: str = "default"):
        self.profile = profile
        self.service_name = "google-personal-mcp"

    def save_credentials(self, creds: dict):
        """Save credentials.json to keyring."""
        keyring.set_password(
            f"{self.service_name}:credentials",
            self.profile,
            json.dumps(creds)
        )

    def load_credentials(self) -> dict:
        """Load credentials.json from keyring."""
        creds_json = keyring.get_password(
            f"{self.service_name}:credentials",
            self.profile
        )
        if creds_json is None:
            raise KeyError(f"Credentials not found for profile {self.profile}")
        return json.loads(creds_json)

    def save_token(self, token: dict):
        """Save token.json to keyring."""
        keyring.set_password(
            f"{self.service_name}:token",
            self.profile,
            json.dumps(token)
        )

    def load_token(self) -> dict:
        """Load token.json from keyring."""
        token_json = keyring.get_password(
            f"{self.service_name}:token",
            self.profile
        )
        if token_json is None:
            raise KeyError(f"Token not found for profile {self.profile}")
        return json.loads(token_json)
```

**Usage:**

```python
# In AuthManager
def get_token_path(self, profile: str = "default") -> str:
    try:
        store = KeyringCredentialStore(profile)
        token_dict = store.load_token()
        # Cache in memory and use
        self._token_cache = token_dict
        return None  # Signal that we have token in memory
    except KeyError:
        # Fall back to file-based
        return os.path.join(config_dir, "token.json")
```

**Testing Challenges:**
- Mocking `keyring` module
- Testing in CI/CD without keyring daemon
- Cross-platform testing

**Deployment Note:** CI/CD pipelines (GitHub Actions) won't have keyring available by default. Need fallback or skip credential-based tests.

---

#### Approach B: File-Based Encryption

Encrypt credentials using a key derived from user's password or master key.

**Library:** `cryptography` package

**Pros:**
- Works everywhere (no OS dependencies)
- Portable (move config across machines)
- Deterministic encryption (same key produces same ciphertext)
- Familiar pattern (many apps use this)

**Cons:**
- Encryption key must be stored/derived (creates new problem: where to store key?)
- Could be stored in keyring (defeats purpose), environment variable (leaks in process list), or derived from password (requires password prompt on startup)
- More complex encryption/decryption logic
- Requires key rotation strategy

**Implementation Outline:**

```python
from cryptography.fernet import Fernet
import base64
import hashlib

class FileEncryptedCredentialStore:
    def __init__(self, profile: str = "default", master_key: str = None):
        self.profile = profile
        self.master_key = master_key or self._derive_master_key()
        self.cipher = Fernet(base64.urlsafe_b64encode(
            hashlib.sha256(self.master_key.encode()).digest()[:32].ljust(32, b'\0')
        ))

    def _derive_master_key(self) -> str:
        """Derive key from user input or keyring (circular dependency!)."""
        # Option 1: Ask user for password on startup (annoying)
        # Option 2: Store in keyring (defeats purpose)
        # Option 3: Use user's login password (requires PAM, complex)
        pass

    def save_token(self, token: dict):
        """Encrypt and save token.json."""
        plaintext = json.dumps(token).encode()
        encrypted = self.cipher.encrypt(plaintext)

        token_path = os.path.join(config_dir, "token.json.enc")
        with open(token_path, 'wb') as f:
            f.write(encrypted)

    def load_token(self) -> dict:
        """Decrypt token.json."""
        token_path = os.path.join(config_dir, "token.json.enc")
        with open(token_path, 'rb') as f:
            encrypted = f.read()

        plaintext = self.cipher.decrypt(encrypted)
        return json.loads(plaintext)
```

**Key Derivation Options:**

1. **Prompt for password:** User types password on startup (annoying but simple)
2. **Keyring-based:** Store master key in keyring (defeats purpose of encryption, but acceptable for extra layer)
3. **Linux PAM:** Use system password (complex, Linux-only, requires privileges)
4. **Deterministic from username:** User+hostname hash (weak security)

**Migration Challenge:** Existing unencrypted tokens → encrypted tokens. Need one-time migration on first run.

---

#### Approach C: Hybrid (Recommended for Phase 2)

**Primary:** Keyring (most secure)
**Fallback:** File-encrypted (works everywhere)
**Fallback:** Plain text (for compatibility, warn user)

```python
def get_token(self, profile: str = "default") -> dict:
    """Load token, trying secure methods first."""

    # Try 1: OS Keyring
    try:
        store = KeyringCredentialStore(profile)
        return store.load_token()
    except (ImportError, KeyError):
        pass

    # Try 2: File-encrypted
    try:
        store = FileEncryptedCredentialStore(profile)
        return store.load_token()
    except (FileNotFoundError, DecryptionError):
        pass

    # Try 3: Plain text (legacy, warn user)
    try:
        logger.warning(f"Using unencrypted token for profile {profile}. Consider enabling encryption.")
        return self._load_plain_text_token(profile)
    except FileNotFoundError:
        raise AuthenticationError(f"No token found for profile {profile}")
```

### Configuration

Add to `config.json`:

```json
{
  "encryption": {
    "enabled": true,
    "method": "keyring",  // or "file-encrypted"
    "fallback_allowed": true
  }
}
```

### Testing Strategy

1. **Unit tests:** Mock keyring and cryptography
2. **Integration tests:** Test with real keyring (skip if unavailable)
3. **CI/CD:** Use plain text fallback for tests, warn about security

### Implementation Priority

**Phase 2:** Design and implement hybrid approach with proper fallbacks and migrations.

---

## 2. Extension & Plugin System

### Context

Currently, tools are hardcoded in `src/google_personal_mcp/server.py`. Users cannot add custom tools without modifying the server code.

### Goals

1. Allow third-party tools without server restart
2. Enable custom services beyond Sheets/Drive
3. Support plugin discovery and registration
4. Enable community contributions

### Design: Tool Plugin Architecture

#### Tool Base Class

```python
# src/google_mcp_core/tools/base.py

from abc import ABC, abstractmethod
from typing import Any, Dict

class Tool(ABC):
    """Base class for MCP tools."""

    name: str = None  # Must be implemented by subclass
    description: str = None
    category: str = "general"  # sheets, drive, calendar, gmail, etc.

    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute tool logic."""
        pass

    @abstractmethod
    def validate_parameters(self, **kwargs) -> bool:
        """Validate input parameters."""
        pass

    def get_schema(self) -> Dict[str, Any]:
        """Return JSON schema for tool parameters."""
        pass
```

#### Built-in Tools as Plugins

Refactor existing tools to inherit from `Tool`:

```python
# src/google_mcp_core/tools/sheets_tools.py

class ListSheetsTool(Tool):
    name = "list_sheets"
    description = "List all sheets in a spreadsheet"
    category = "sheets"

    def execute(self, sheet_alias: str) -> Dict[str, Any]:
        # Existing implementation
        pass
```

#### Tool Registry

```python
# src/google_mcp_core/tools/registry.py

class ToolRegistry:
    """Central registry for all available tools."""

    def __init__(self):
        self.tools: Dict[str, Tool] = {}

    def register(self, tool: Tool):
        """Register a tool."""
        if tool.name in self.tools:
            raise ValueError(f"Tool {tool.name} already registered")
        self.tools[tool.name] = tool

    def get_tool(self, name: str) -> Tool:
        """Get tool by name."""
        return self.tools.get(name)

    def list_tools(self, category: str = None) -> List[Tool]:
        """List all tools, optionally filtered by category."""
        if category:
            return [t for t in self.tools.values() if t.category == category]
        return list(self.tools.values())

    def load_plugins_from_directory(self, directory: str):
        """Dynamically load tools from a directory."""
        for path in Path(directory).glob("*.py"):
            # Import module and register tools
            pass
```

#### Plugin Discovery via Entry Points

In `pyproject.toml`:

```toml
[project.entry-points."google_personal_mcp.tools"]
list_sheets = "google_mcp_core.tools.sheets_tools:ListSheetsTool"
get_prompts = "google_mcp_core.tools.sheets_tools:GetPromptsTool"
list_files = "google_mcp_core.tools.drive_tools:ListFilesTool"
```

#### Usage in Server

```python
# src/google_personal_mcp/server.py

from google_mcp_core.tools.registry import ToolRegistry

registry = ToolRegistry()

# Load built-in tools
registry.register(ListSheetsTool())
registry.register(GetPromptsTool())
# ... etc

# Load plugins from entry points
for tool_class in pkg_resources.iter_entry_points('google_personal_mcp.tools'):
    tool = tool_class()
    registry.register(tool)

# Load user plugins from directory
if os.path.exists(PLUGINS_DIR):
    registry.load_plugins_from_directory(PLUGINS_DIR)

# Register with MCP server
for tool in registry.list_tools():
    @mcp.tool()
    def tool_wrapper(**kwargs):
        return tool.execute(**kwargs)
```

### Example: Custom Tool

```python
# ~/.config/google-personal-mcp/plugins/archive_tool.py

from google_mcp_core.tools import Tool
from datetime import datetime

class ArchiveSheetTool(Tool):
    name = "archive_sheet"
    description = "Archive a sheet by copying to folder and deleting original"
    category = "sheets"

    def execute(self, sheet_alias: str, archive_folder_alias: str, **kwargs) -> Dict:
        try:
            # Get sheet service
            sheet_service, spreadsheet_id = get_sheets_service(sheet_alias)

            # Copy sheet to folder
            # ... implementation ...

            return {"status": "success", "message": "Sheet archived"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
```

### Benefits

1. Users can add tools without modifying server code
2. Community can contribute tools as separate packages
3. Decoupling: core server separate from tools
4. Tool versioning independent of server version

### Risks

1. Security: arbitrary code execution (plugins could do anything)
2. Compatibility: plugins may break on server updates
3. Discovery: how do users find plugins?

### Mitigations

1. **Security:** Document that plugins run with user's credentials
2. **Compatibility:** Establish stable Tool interface, semantic versioning
3. **Discovery:** Create plugin registry/marketplace (GitHub topic: `google-personal-mcp-plugin`)

### Implementation Timeline

**Phase 2:** Prototype with built-in tools as plugins
**Phase 3:** Enable user-provided plugins, create example plugin repository

---

## 3. Async Tool Execution for MCP Server

### Context

Current implementation:
```python
def main():
    import anyio
    anyio.run(async_main)

async def async_main():
    await mcp.run_stdio_async()
```

The MCP protocol is async, but individual tool implementations are sync. When a tool makes a slow API call, it blocks the async event loop, preventing concurrent tool calls.

### Problem

**Scenario:** Agent calls `upload_file` (10 seconds) and `list_sheets` (2 seconds) in parallel.
- **Current:** Sequential execution (12 seconds total)
- **Desired:** Parallel execution (10 seconds total)

### Solution: Async Tool Definitions

Rewrite tools as async functions:

```python
# Option 1: Direct async tools
@mcp.tool()
async def list_sheets(sheet_alias: str) -> dict:
    """Lists all sheets (tabs) in a given spreadsheet."""
    try:
        service, spreadsheet_id = await get_sheets_service_async(sheet_alias)
        sheets = await service.list_sheet_titles_async(spreadsheet_id)
        return {"status": "success", "sheets": sheets}
    except Exception as e:
        return {"status": "error", "message": str(e)}
```

### Challenges

1. **Google API Library:** `google-api-python-client` is synchronous
   - Need wrapper: `asyncio.to_thread(blocking_call)` or use async library
   - Option: Use `aiohttp` instead of `httpx` for async HTTP
   - Option: Use `google-cloud-python` (fully async version)

2. **Service Layer:** All service classes must be async
   ```python
   class SheetsService:
       async def list_sheet_titles(self, spreadsheet_id: str) -> List[str]:
           # Implementation using async API calls
           pass
   ```

3. **Testing:** Async tests require `pytest-asyncio`, more complex mocking

4. **Compatibility:** Code cannot mix sync and async (all or nothing)

### Research Needed

1. **Google API async support:** Investigate `google-cloud-python` async APIs
2. **Performance impact:** Profile parallel vs sequential
3. **Complexity cost:** Estimate refactoring effort (3-4 weeks?)
4. **MCP server maturity:** Verify if async tools are production-ready

### Recommendation for Phase 2

1. **Benchmark:** Measure if parallelism is actually needed (agents usually call one tool at a time)
2. **Prototype:** If needed, start with one service (DriveService) as proof-of-concept
3. **Decide:** Async only if performance analysis justifies the complexity

### Example Implementation (Proof of Concept)

```python
# Using asyncio to wrap sync calls
from concurrent.futures import ThreadPoolExecutor
import asyncio

executor = ThreadPoolExecutor(max_workers=4)

async def list_sheets_async(sheet_alias: str) -> dict:
    """Async version using thread pool."""
    try:
        loop = asyncio.get_event_loop()
        service, spreadsheet_id = await loop.run_in_executor(
            executor,
            get_sheets_service,
            sheet_alias
        )

        titles = await loop.run_in_executor(
            executor,
            service.list_sheet_titles,
            spreadsheet_id
        )

        return {"status": "success", "sheets": titles}
    except Exception as e:
        return {"status": "error", "message": str(e)}
```

**Pros:** Simple wrapper, maintains existing service classes
**Cons:** Still uses thread pool (GIL bottleneck), doesn't provide true async benefits

---

## 4. Performance Optimization

### 4.1 Caching Layer

**Goal:** Reduce API calls for frequently-accessed data

**Strategy:**
- Cache sheet metadata (tabs, column count) with TTL (5 minutes)
- Cache folder listings with TTL (10 minutes)
- Provide cache invalidation via `refresh_config` tool

**Implementation:**

```python
from functools import lru_cache
from datetime import datetime, timedelta

class CacheManager:
    def __init__(self, ttl_seconds: int = 300):
        self.ttl = ttl_seconds
        self.cache: Dict[str, Tuple[Any, float]] = {}

    def get(self, key: str) -> Optional[Any]:
        """Get cached value if not expired."""
        if key not in self.cache:
            return None

        value, timestamp = self.cache[key]
        if datetime.now().timestamp() - timestamp > self.ttl:
            del self.cache[key]
            return None

        return value

    def set(self, key: str, value: Any):
        """Cache value with current timestamp."""
        self.cache[key] = (value, datetime.now().timestamp())

    def clear(self, pattern: str = None):
        """Clear cache entries matching pattern."""
        if pattern is None:
            self.cache.clear()
            return

        keys_to_delete = [k for k in self.cache.keys() if pattern in k]
        for k in keys_to_delete:
            del self.cache[k]
```

### 4.2 Pagination Support

**Goal:** Handle large file listings and spreadsheets

**Strategy:**
- Add `offset` and `limit` parameters to list operations
- Return `has_more` flag to indicate more results available
- Paginate automatically behind the scenes (load next page on scroll/request)

**Implementation:**

```python
def list_drive_files(
    folder_alias: str,
    offset: int = 0,
    limit: int = 100
) -> dict:
    """List files in a folder with pagination."""
    service, folder_id = get_drive_service(folder_alias)

    query = f"'{folder_id}' in parents and trashed = false"
    results = service.service.files().list(
        q=query,
        spaces='drive',
        pageSize=limit,
        fields='nextPageToken, files(id, name, mimeType, size, modifiedTime)',
        pageToken=None  # Get first page
    ).execute()

    files = results.get('files', [])
    has_more = 'nextPageToken' in results

    return {
        "status": "success",
        "files": files,
        "count": len(files),
        "has_more": has_more,
        "next_token": results.get('nextPageToken')
    }
```

### 4.3 Connection Pooling

**Goal:** Reuse HTTP connections

**Strategy:**
- Use connection pool for HTTP requests (already done via `httpx`)
- Reuse service instances across tool calls (already done via `GoogleContext`)
- Consider persistent connection to Google APIs

**Current State:** Already partially implemented
- `GoogleContext` caches service instances: `self._services[(name, version)]`
- `httpx` uses connection pool by default

**Future:** Monitor connection pool metrics, adjust pool size if needed

---

## 5. Operational Concerns

### 5.1 Rate Limiting Detection & Backoff

**Goal:** Detect when Google API rate limits are hit and backoff gracefully

**Strategy:**
- Detect 429 (Too Many Requests) responses
- Implement exponential backoff (already covered in Phase 1 as retry logic)
- Inform agent about rate limiting
- Proactively warn about approaching limits

**Implementation:**

```python
class RateLimiter:
    def __init__(self):
        self.last_reset = datetime.now()
        self.requests_this_minute = 0
        self.requests_per_minute = 600  # Google Sheets API limit

    def check_limit(self):
        """Check if rate limit is approaching."""
        now = datetime.now()
        if (now - self.last_reset).total_seconds() > 60:
            self.requests_this_minute = 0
            self.last_reset = now

        self.requests_this_minute += 1

        if self.requests_this_minute > self.requests_per_minute:
            raise RateLimitError("Rate limit exceeded")
        elif self.requests_this_minute > self.requests_per_minute * 0.8:
            logger.warning(f"Approaching rate limit: {self.requests_this_minute}/{self.requests_per_minute}")
```

### 5.2 Quota Management

**Goal:** Track and report API quota usage

**Strategy:**
- Track daily/monthly quota per service
- Return quota info in health check
- Warn when approaching limits

**Implementation:**

```python
class QuotaTracker:
    def __init__(self):
        self.quota_usage: Dict[str, int] = {}

    def increment_usage(self, service: str, amount: int = 1):
        """Track API call."""
        if service not in self.quota_usage:
            self.quota_usage[service] = 0
        self.quota_usage[service] += amount

    def get_usage(self, service: str) -> int:
        """Get usage for service."""
        return self.quota_usage.get(service, 0)

    def get_quota_status(self) -> dict:
        """Return quota status for all services."""
        return {
            "sheets": {
                "usage": self.get_usage("sheets"),
                "limit": 60000,  # Writes per day
                "percent_used": (self.get_usage("sheets") / 60000) * 100
            },
            "drive": {
                "usage": self.get_usage("drive"),
                "limit": 1000000,  # Varies by project
                "percent_used": (self.get_usage("drive") / 1000000) * 100
            }
        }
```

### 5.3 Graceful Degradation / Circuit Breaker

**Goal:** If one API fails, others continue to work

**Strategy:**
- Implement circuit breaker pattern: fail fast after repeated failures
- Per-API circuit breakers (Sheets separate from Drive)
- Return partial results with warnings

**Implementation:**

```python
from enum import Enum

class CircuitState(Enum):
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing recovery

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, reset_timeout: int = 60):
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.last_failure_time = None

    def call(self, func, *args, **kwargs):
        """Call function through circuit breaker."""
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
            else:
                raise CircuitBreakerError("Circuit is open")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise

    def _on_success(self):
        self.failure_count = 0
        self.state = CircuitState.CLOSED

    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN

    def _should_attempt_reset(self) -> bool:
        return (
            self.last_failure_time and
            (datetime.now() - self.last_failure_time).total_seconds() > self.reset_timeout
        )
```

---

## 6. Configuration Evolution

### Multiple Configuration Formats (YAML, TOML)

**Goal:** Support more user-friendly config formats

**Options:**
- **JSON:** Current (verbose, strict)
- **YAML:** Human-friendly (indentation-sensitive, can be ambiguous)
- **TOML:** Explicit, less ambiguous than YAML, good for mixed types

**Pros:**
- YAML/TOML easier to write than JSON
- Can add comments in YAML/TOML
- Familiar to Kubernetes/DevOps users

**Cons:**
- Additional parser libraries
- YAML indentation issues (common source of bugs)
- Minimal benefit over JSON with good formatting

**Recommendation:** Skip for now. JSON is sufficient and more portable. If needed in Phase 2, only add TOML support (skip YAML).

### Environment-Based Configuration Profiles

**Goal:** Support dev/test/prod configurations

**Current:** `config.json` is global

**Future:** `config.{ENVIRONMENT}.json` with environment-specific overrides

```bash
# Development
export GOOGLE_MCP_ENV=dev
# Loads: ~/.config/google-personal-mcp/config.dev.json
# Falls back to: ~/.config/google-personal-mcp/config.json

# Production
export GOOGLE_MCP_ENV=prod
# Loads: ~/.config/google-personal-mcp/config.prod.json
```

**Implementation:**
- Check `GOOGLE_MCP_ENV` environment variable
- Load environment-specific config if present
- Merge with base config (environment config overrides base)

---

## 7. Observability Enhancements

### Request Tracing Integration

**Goal:** Integrate with external tracing services (Jaeger, Zipkin, etc.)

**Strategy:**
- Export request IDs to tracing backend
- Track request flow through services
- Identify slow operations

### Metrics Exportation

**Goal:** Export Prometheus-style metrics

**Strategy:**
- Tool call counts
- API call latencies (histograms)
- Error rates
- Cache hit/miss rates

**Implementation:** Use `prometheus-client` library

### Alerting

**Goal:** Alert on errors, rate limits, quota exhaustion

**Strategy:**
- Integration with alerting systems (PagerDuty, Slack, etc.)
- Configurable alert thresholds

---

## Summary: Implementation Roadmap

| Phase | Features | Timeline |
|-------|----------|----------|
| **Phase 1** | Security, testing, docs, observability | ✅ Current session |
| **Phase 2** | Encryption, plugins, async proto, perf | Q1 2025 |
| **Phase 3** | Tracing, metrics, alerting | Q2 2025 |
| **Phase 4** | Additional Google APIs (Gmail, Calendar, Docs) | Q3 2025 |

---

## Decision Framework for Future Features

When considering new features:

1. **Impact:** Will this help agents complete tasks faster/better?
2. **Complexity:** How much code/testing is needed?
3. **Maintenance:** Will this increase ongoing maintenance burden?
4. **Security:** Does this introduce security risks?
5. **Compatibility:** Will this break existing configurations?

**High Priority:** High impact, low complexity, no security risks
**Medium Priority:** Medium impact, medium complexity, or minor security implications
**Low Priority:** Low impact, high complexity, or maintenance burden

All Phase 1 items are high priority. Phase 2 items require more justification based on user feedback.
