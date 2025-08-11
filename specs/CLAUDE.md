# Trove SDK Project Specifications

## Project Overview

This project implements a lean, well-typed Python SDK for the Trove v3 API and a separate MCP server. The goal is to create research-friendly tools for accessing Australia's National Library Trove digital collection.

**Architecture**: Two packages in a monorepo:
- `packages/trove-sdk/` - Python library (sync+async, caching, rate limiting, citations)  
- `packages/trove-mcp/` - MCP server adapter wrapping the SDK

## Files in This Directory

- **[DESIGN.md](./DESIGN.md)** - Overall architecture and high-level delivery plan
- **[ROLLOUT_PLAN.md](./ROLLOUT_PLAN.md)** - Detailed staged implementation timeline with risk assessment
- **[STAGE_1_FOUNDATION_DESIGN.md](./STAGE_1_FOUNDATION_DESIGN.md)** - Transport layer, config, errors foundation
- **[STAGE_2_COMPLETE_SEARCH_DESIGN.md](./STAGE_2_COMPLETE_SEARCH_DESIGN.md)** - Raw search API with full parameter support
- **[STAGE_3_CORE_RESOURCES_DESIGN.md](./STAGE_3_CORE_RESOURCES_DESIGN.md)** - Individual record access endpoints
- **[STAGE_4_ERGONOMIC_SEARCH_DESIGN.md](./STAGE_4_ERGONOMIC_SEARCH_DESIGN.md)** - Fluent builder API for search
- **[STAGE_5_CITATIONS_DESIGN.md](./STAGE_5_CITATIONS_DESIGN.md)** - PID management and citation export
- **[STAGE_6_MODELS_POLISH_DESIGN.md](./STAGE_6_MODELS_POLISH_DESIGN.md)** - Optional Pydantic models and production polish
- **[STAGE_7_MCP_SERVER_DESIGN.md](./STAGE_7_MCP_SERVER_DESIGN.md)** - MCP server implementation

## Master Implementation Checklist

### Stage 1 - Foundation (Transport, Config, Errors)
- [x] **Core Infrastructure**
  - [x] httpx-based transport layer (sync/async)
  - [x] API key authentication via `X-API-KEY` header
  - [x] Configuration management (`TroveConfig` class)
  - [x] Structured exception hierarchy
  - [x] Request/response logging with credential redaction
- [x] **Rate Limiting**
  - [x] Token bucket algorithm implementation
  - [x] Conservative default limits (2 req/sec, burst 5)
  - [x] Respect `Retry-After` headers
  - [x] Exponential backoff with jitter
- [x] **Caching**  
  - [x] Basic memory cache implementation
  - [x] Pluggable `CacheBackend` interface
  - [x] Cache key normalization
- [x] **Testing & CI**
  - [x] First successful `/v3/result` API call
  - [x] Unit tests for all components
  - [x] CI pipeline setup (lint, type checks)
  - [x] Test API key configuration
- [x] **Documentation**
  - [x] README quickstart guide
  - [x] Authentication setup instructions
  - [x] First request example
- [x] **Stage 1 Complete**: ✅ All tests pass, CI green, smoke test works

### Stage 2 - Complete Search (Raw Search API)  
- [ ] **Search Implementation**
  - [x] Complete `SearchResource.page(**params)` method
  - [x] Support all 60+ search parameters from API docs
  - [x] Parameter validation and type checking
  - [x] `params.build_limits` utility function
- [ ] **Pagination**
  - [x] Single-category cursor pagination iterators
  - [x] `iter_pages` and `iter_records` methods
  - [x] Multi-category pagination documentation
  - [x] Clear error messages for multi-category limitations
- [ ] **Enhanced Caching**
  - [x] SQLite persistent cache implementation  
  - [x] Route-based TTL configuration
  - [x] Cache statistics and monitoring
- [ ] **Testing**
  - [x] All search parameters validated
  - [x] Single-category pagination verified
  - [x] Cache effectiveness measured
  - [x] Example queries in CI
- [ ] **Documentation**
  - [x] Complete searching guide (categories, limits, cursors)
  - [x] Caching and rate limiting usage
  - [x] Multi-category behavior explanation
- [x] **Stage 2 Complete**: ✅ All search params work, pagination reliable, examples pass

### Stage 3 - Core Resources (Individual Record Access)
- [ ] **Resource Endpoints**
  - [ ] Work resource (`/v3/work/{id}`)
  - [ ] Newspaper article resource (`/v3/newspaper/{id}`)
  - [ ] Gazette article resource (`/v3/gazette/{id}`)
  - [ ] People/organization resource (`/v3/people/{id}`)
  - [ ] List resource (`/v3/list/{id}`)
  - [ ] Title resources (newspaper, magazine, gazette)
- [ ] **Parameter Support**
  - [ ] Full support for `include` parameter
  - [ ] Full support for `reclevel` parameter  
  - [ ] Full support for `encoding` parameter
- [ ] **Error Handling**
  - [ ] Proper 404 handling for missing records
  - [ ] 429 rate limit handling
  - [ ] All documented error cases covered
- [ ] **Testing**
  - [ ] Contract tests for all endpoints
  - [ ] Error scenario testing
  - [ ] Parameter validation tests
- [ ] **Documentation**
  - [ ] Resource pages with examples for each endpoint
  - [ ] Include/reclevel usage patterns
  - [ ] Error handling examples
- [ ] **Stage 3 Complete**: ✅ All core endpoints accessible, robust error handling

### Stage 4 - Ergonomic Search (Fluent Builder API)
- [ ] **Builder Implementation**
  - [ ] Immutable `Search` builder class
  - [ ] `.text()` method for query text
  - [ ] `.in_()` method for categories
  - [ ] `.page_size()` method for pagination
  - [ ] `.sort()` method for result ordering
  - [ ] `.with_reclevel()` method for record detail
  - [ ] `.with_facets()` method for facet inclusion
  - [ ] `.where()` method for additional filters
  - [ ] `.harvest()` method for bulk operations
- [ ] **Result Methods**
  - [ ] `.first_page()` for single page results
  - [ ] `.pages()` iterator for all pages
  - [ ] `.records()` iterator for all records
- [ ] **Multi-category Handling**
  - [ ] Clear error messages for unsupported operations
  - [ ] Documentation of limitations
  - [ ] Per-category helper methods
- [ ] **Testing**
  - [ ] Builder methods compile correctly to raw parameters
  - [ ] Single-category flows work seamlessly
  - [ ] Parity testing with raw API
- [ ] **Documentation**
  - [ ] Ergonomic vs raw API comparison
  - [ ] Three runnable examples demonstrating benefits
  - [ ] Multi-category limitation explanations
- [ ] **Stage 4 Complete**: ✅ Fluent API works, examples demonstrate value

### Stage 5 - Citations (PID Management & Export)
- [ ] **PID Extraction**
  - [ ] PID extractors for all record types (Work, Article, People, List, Title)
  - [ ] URL pattern recognition for Trove URLs
  - [ ] Canonical PID format validation
- [ ] **Resolution System**
  - [ ] PID to record resolution
  - [ ] URL to record resolution  
  - [ ] Search-based fallback for ambiguous cases
  - [ ] Handle malformed PIDs gracefully
- [ ] **Citation Formatters**
  - [ ] BibTeX citation formatter
  - [ ] CSL-JSON citation formatter
  - [ ] Validate output formats
- [ ] **Testing**
  - [ ] Round-trip tests (record → PID → record)
  - [ ] Citation formatter validation
  - [ ] Edge case handling
  - [ ] Real data testing
- [ ] **Documentation**
  - [ ] Citing Trove guide with canonical PID examples
  - [ ] Citation format examples
  - [ ] PID resolution patterns
- [ ] **Stage 5 Complete**: ✅ Citation system works end-to-end with real data

### Stage 6 - Models & Polish (Production Ready)
- [ ] **Optional Models**
  - [ ] Pydantic models for common response types
  - [ ] `.raw` access always available
  - [ ] Type safety without breaking flexibility
- [ ] **Production Features**
  - [ ] Enhanced error messages with debugging info
  - [ ] Performance optimizations
  - [ ] Production logging configuration
  - [ ] Type stub files for IDE support
- [ ] **Documentation Polish**
  - [ ] Complete API reference documentation
  - [ ] Documentation site build automation
  - [ ] All examples verified to execute
  - [ ] Troubleshooting guide
  - [ ] Changelog for v1.0
- [ ] **Quality Assurance**
  - [ ] Performance benchmarks meet targets
  - [ ] >90% test coverage maintained
  - [ ] Package ready for PyPI publication
- [ ] **Stage 6 Complete**: ✅ Production-ready with complete documentation

### Stage 7 - MCP Server (Separate Package)
- [ ] **Package Structure**
  - [ ] Separate `trove-mcp` package
  - [ ] Independent versioning from SDK
  - [ ] Proper dependency management
- [ ] **MCP Tools**
  - [ ] `trove.search_page` tool
  - [ ] `trove.get_work` tool
  - [ ] `trove.get_article` tool  
  - [ ] `trove.get_people` tool
  - [ ] `trove.get_list` tool
  - [ ] `trove.get_title` tool
  - [ ] `trove.resolve_pid` tool
  - [ ] `trove.citation` tool
- [ ] **Integration Features**
  - [ ] Shared cache/rate limiter with SDK
  - [ ] Stateless pagination handling
  - [ ] JSON schema validation for all tools
  - [ ] Environment-only configuration (security)
- [ ] **Testing**
  - [ ] Contract tests verify tool schemas
  - [ ] E2E testing with mock transport
  - [ ] MCP protocol compliance testing
- [ ] **Documentation**
  - [ ] MCP server quickstart guide
  - [ ] Tool schema documentation
  - [ ] Deployment instructions
- [ ] **Stage 7 Complete**: ✅ MCP server fully functional and documented

## Rollout Instructions

### Development Process
1. **Read API Documentation**: Before starting each stage, carefully review all relevant files in `@api_docs/` as described in `@api_docs/CLAUDE.md`
2. **Follow Specifications**: If stage specs don't match API docs, prefer API docs. Document any departures and stop implementation
3. **One Stage Per Commit**: Each stage is a single git commit - no commits until stage is complete
4. **All Tests Must Pass**: Never commit failing tests or incomplete functionality
5. **Mark Progress**: Check off completed items in this checklist as work progresses, not at the end of stages

### Definition of Done (Per Stage)
Each stage is complete only when:
- ✅ All deliverables implemented according to specifications
- ✅ All tests pass (unit, integration, relevant E2E)
- ✅ Documentation updated and examples work
- ✅ Code reviewed and approved
- ✅ CI pipeline completely green
- ✅ Performance requirements met
- ✅ No security issues or credential leaks

### Quality Gates
- **Test Coverage**: Maintain >90% throughout all stages
- **API Compatibility**: All examples must work with real Trove API
- **Documentation**: All examples must execute successfully
- **Performance**: <2s response times, <100MB memory usage for typical workloads

### Rollback Strategy  
- Each stage gets a version tag for easy rollback
- Maintain backward compatibility between stages
- Document any breaking changes clearly
- Provide migration guides when needed

---

This checklist serves as the master tracking document for the entire project. Check off items as they are completed to maintain clear progress visibility and enable easy resumption of work.