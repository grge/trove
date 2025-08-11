# Trove v3 SDK - Staged Rollout Plan

Based on the architecture outlined in DESIGN.md and comprehensive review of the API documentation, this document provides a detailed staged implementation plan for the Trove v3 Python SDK and MCP Server.

## Overview

The implementation is divided into 7 stages, each with clear deliverables, definition of done criteria, and comprehensive testing plans. Each stage builds upon the previous ones, ensuring we have a working, tested foundation at each step.

## Stage Dependencies

```
Stage 1 (Foundation) 
    ↓
Stage 2 (Complete Search)
    ↓
Stage 3 (Core Resources)
    ↓
Stage 4 (Ergonomic Search)
    ↓
Stage 5 (Citations)
    ↓
Stage 6 (Models & Polish)
    ↓
Stage 7 (MCP Server)
```

## Risk Assessment

**High Risk Areas:**
- Rate limiting implementation (Stage 1)
- Multi-category pagination handling (Stage 2)
- PID extraction and resolution (Stage 5)

**Mitigation Strategies:**
- Real API testing with conservative rate limits
- Comprehensive pagination test suite
- Pattern-based PID extraction with fallback search
- Pass-through parameters for future API changes

## Implementation Timeline Estimate

- **Stage 1-3**: 2-3 weeks (core functionality)
- **Stage 4-5**: 1-2 weeks (convenience features)
- **Stage 6**: 1 week (polish and docs)
- **Stage 7**: 1 week (MCP server)

**Total: 5-7 weeks** for complete implementation

## Stage Rollout Details

### Stage 1 - Foundation (Transport, Config, Errors)
**Duration**: 4-5 days
**Risk**: Medium (rate limiting complexity)

#### Deliverables
- httpx-based transport layer (sync/async)
- API key authentication via `X-API-KEY` header
- Rate limiting with token bucket algorithm
- Basic memory cache implementation
- Structured exception hierarchy
- Configuration management
- Request/response logging (with credential redaction)

#### Success Criteria
- First successful `/v3/result` API call
- Rate limiting prevents 429 errors
- All exceptions properly structured
- CI pipeline green (lint, type checks, basic tests)

---

### Stage 2 - Complete Search (Raw Search API)
**Duration**: 5-6 days  
**Risk**: High (multi-category pagination complexity)

#### Deliverables
- Complete `SearchResource.page(**params)` implementation
- All search parameters supported (60+ params from API docs)
- Single-category cursor pagination iterators
- Multi-category pagination documentation and warnings
- SQLite persistent cache implementation
- Route-based TTL configuration

#### Success Criteria
- All search parameters from API docs supported
- Single-category pagination works reliably
- Cache reduces API calls measurably
- Comprehensive parameter validation
- Examples run successfully in CI

---

### Stage 3 - Core Resources (Individual Record Access)
**Duration**: 4-5 days
**Risk**: Low (straightforward CRUD operations)

#### Deliverables
- Work resource (`/v3/work/{id}`)
- Newspaper article resource (`/v3/newspaper/{id}`)
- Gazette article resource (`/v3/gazette/{id}`)
- People/organization resource (`/v3/people/{id}`)
- List resource (`/v3/list/{id}`)
- Title resources (newspaper, magazine, gazette titles)
- Full support for `include`, `reclevel`, `encoding` parameters

#### Success Criteria
- All core endpoints accessible
- Proper 404 handling for missing records
- Include parameters work correctly
- Error handling covers all documented error cases
- Contract tests verify API compatibility

---

### Stage 4 - Ergonomic Search (Fluent Builder API)
**Duration**: 3-4 days
**Risk**: Low (builds on Stage 2)

#### Deliverables
- Immutable `Search` builder class
- Methods: `.text()`, `.in_()`, `.page_size()`, `.sort()`, `.with_reclevel()`, `.with_facets()`, `.where()`, `.harvest()`
- Result methods: `.first_page()`, `.pages()`, `.records()`
- Multi-category handling with clear error messages
- Compilation to raw parameters

#### Success Criteria
- Fluent API compiles correctly to raw parameters
- Single-category flows work seamlessly
- Multi-category limitations clearly documented
- Parity with raw API for supported use cases
- Examples demonstrate ergonomic advantages

---

### Stage 5 - Citations (PID Management & Export)
**Duration**: 3-4 days
**Risk**: Medium (PID extraction patterns may be incomplete)

#### Deliverables
- PID extraction from all record types
- URL/PID pattern recognition
- Search-based PID resolution fallback
- BibTeX citation formatter
- CSL-JSON citation formatter
- Canonical URL generation

#### Success Criteria
- PID extraction works for all core record types
- Round-trip tests (record → PID → record) pass
- BibTeX and CSL-JSON outputs validate
- Handles edge cases and malformed PIDs gracefully
- Citation examples work with real data

---

### Stage 6 - Models & Polish (Optional Types & Production Ready)
**Duration**: 3-4 days
**Risk**: Low (polish phase)

#### Deliverables
- Optional Pydantic models for common response types
- Enhanced error messages and debugging info
- Performance optimizations
- Complete API reference documentation
- Production logging configuration
- Type stub files for better IDE support

#### Success Criteria
- Models provide type safety without breaking raw access
- Documentation site builds and deploys
- Performance benchmarks meet targets
- All examples in docs execute successfully
- Package ready for PyPI publication

---

### Stage 7 - MCP Server (Separate Package)
**Duration**: 4-5 days
**Risk**: Medium (MCP protocol integration)

#### Deliverables
- Separate `trove-mcp` package
- MCP tools: `search_page`, `get_*`, `resolve_pid`, `citation`
- Stateless pagination handling
- Shared cache/rate limiter with SDK
- JSON schema validation for all tools
- Configuration via environment variables only

#### Success Criteria
- All MCP tools work with real API data
- Stateless pagination maintains consistency
- Error handling preserves SDK error information
- Contract tests verify tool schemas
- Deployment ready with proper security

## Quality Assurance Strategy

### Unit Testing
- **Coverage Target**: >90% line coverage
- **Test Types**: Pure unit tests, no external API calls
- **Mock Strategy**: Mock transport layer, test business logic
- **Property Testing**: Use Hypothesis for parameter validation

### Integration Testing  
- **Real API Testing**: Use actual Trove API with test API key
- **Rate Limiting**: Verify respectful API usage
- **Error Scenarios**: Test all documented error conditions
- **Multi-category**: Comprehensive pagination testing
- **Caching**: Verify cache behavior and TTL handling

### End-to-End Testing
- **Example Verification**: All documentation examples must run
- **Performance Testing**: Response time and memory usage benchmarks  
- **Compatibility Testing**: Multiple Python versions (3.10+)
- **MCP Integration**: Full MCP server functionality testing

### Documentation Testing
- **Doctest**: Executable examples in docstrings
- **Link Checking**: All external links functional
- **Example Freshness**: Regular testing against live API
- **Accessibility**: Documentation accessible to new users

## Definition of Done (Per Stage)

Each stage is considered complete when:

1. **✅ All deliverables implemented** - Feature-complete according to spec
2. **✅ Tests pass** - Unit, integration, and relevant E2E tests green
3. **✅ Documentation updated** - API docs and examples current
4. **✅ Code reviewed** - Peer review completed
5. **✅ CI pipeline green** - All automated checks passing
6. **✅ Performance verified** - Meets performance requirements
7. **✅ Security reviewed** - No credential leaks or security issues

## Rollback Strategy

Each stage maintains backward compatibility:
- **Version Tagging**: Each stage gets a version tag
- **Feature Flags**: New features can be disabled if needed
- **Graceful Degradation**: Later stages fail gracefully if earlier stages have issues
- **Documentation**: Clear migration guides between versions

## Monitoring and Success Metrics

### Development Metrics
- **Code Coverage**: Maintain >90% throughout
- **API Response Times**: <2s for typical requests
- **Memory Usage**: <100MB for typical workloads
- **Error Rates**: <1% for valid requests

### Usage Metrics (Post-Launch)
- **Adoption**: Downloads and usage statistics
- **Error Monitoring**: Real-world error patterns
- **Performance**: Response times in production use
- **Feedback**: User bug reports and feature requests

## Post-Implementation Plan

### v1.1 Enhancements
- Advanced search DSL
- Facet term objects
- Contributor/partner endpoints
- Performance optimizations

### v2.0 Considerations
- Async-first architecture
- GraphQL-style query builder
- Built-in data visualization helpers
- Machine learning integrations

---

This rollout plan provides a structured approach to implementing the Trove v3 SDK while maintaining high quality standards and managing risk through incremental delivery. Each stage builds confidence for the next, ensuring we deliver a robust, well-tested solution.