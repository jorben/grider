# Design Considerations for add-custom-backtest-parameters

## Architecture Overview

### Current Architecture
The current system uses a fully automated approach where grid strategy parameters are calculated using ATR algorithms. The backtest engine accepts a fixed grid strategy configuration and runs simulations with predefined parameters.

### Proposed Architecture Changes

#### Frontend Architecture
```
AnalysisPage
├── AnalysisReport
    ├── GridParametersCard (display-only)
    ├── BacktestTab
        ├── BacktestConfigEditor (existing - backtest params only)
        └── GridParameterEditor (new - grid strategy params)
```

#### Backend Architecture
```
Backtest API Endpoint
├── Parameter Validation Layer
├── Grid Strategy Builder (new)
    ├── Custom Parameter Mode
    └── Automatic Calculation Mode (existing)
├── Backtest Engine (modified)
    └── Grid Calculator (modified)
```

## Key Design Decisions

### 1. Parameter Separation
**Decision**: Keep backtest parameters (commission rates, risk-free rate) separate from grid strategy parameters (price ranges, step sizes).

**Rationale**:
- Different parameter types serve different purposes
- Backtest parameters are universal across strategies
- Grid parameters are strategy-specific
- Maintains existing BacktestConfigEditor functionality

### 2. Custom vs Automatic Mode
**Decision**: Support both custom parameter input and automatic calculation modes.

**Rationale**:
- Preserves existing automated behavior as default
- Allows advanced users to customize parameters
- Enables A/B testing between automatic and custom approaches
- Maintains backward compatibility

### 3. Real-time Validation
**Decision**: Implement client-side parameter validation with immediate feedback.

**Rationale**:
- Prevents invalid API calls
- Improves user experience with instant feedback
- Reduces server load from invalid requests
- Allows complex validation rules (e.g., price ranges, step size constraints)

### 4. Parameter Persistence
**Decision**: Store custom parameters in session storage with analysis-specific keys.

**Rationale**:
- Parameters are tied to specific analysis sessions
- Avoids polluting localStorage with temporary data
- Enables resuming interrupted analysis sessions
- Automatic cleanup when sessions expire

## Data Flow

### Custom Parameter Backtest Flow
```
1. User opens analysis page
2. System loads default (automatic) parameters
3. User clicks "Edit Grid Parameters"
4. GridParameterEditor loads current parameters
5. User modifies parameters
6. Client validates parameters in real-time
7. User clicks "Apply & Re-run Backtest"
8. Parameters sent to backtest API
9. Backend validates parameters
10. Custom grid strategy created
11. Backtest executed with custom parameters
12. Results displayed to user
```

### Parameter Validation Rules

#### Price Range Validation
- Upper limit > Lower limit
- Lower limit < Current price < Upper limit (recommended)
- Range ratio < 200% (to prevent unrealistic ranges)
- Range ratio > 5% (to ensure meaningful trading opportunities)

#### Investment Amount Validation
- Minimum investment: ¥1,000
- Maximum investment: ¥10,000,000
- Must be divisible by single trade quantity

#### Grid Step Size Validation
- Minimum step: 0.01 (0.01元 for stocks)
- Maximum step: price_range / 2
- Must allow at least 2 grid levels

#### Time Interval Validation
- Start date < End date
- Date range within available data period
- Minimum range: 30 trading days
- Maximum range: 2 years

## Error Handling

### Client-side Validation Errors
- Display inline validation messages
- Prevent form submission with invalid data
- Provide suggestions for valid parameter ranges
- Highlight conflicting parameter combinations

### Server-side Validation Errors
- Return structured error responses
- Include specific parameter validation failures
- Provide suggestions for correction
- Maintain API consistency with existing endpoints

### Backtest Execution Errors
- Handle data unavailability for custom time ranges
- Manage insufficient data scenarios
- Provide fallback to automatic parameters when needed

## Performance Considerations

### Caching Strategy
- Cache backtest results by parameter hash
- Invalidate cache when parameters change
- Limit cache size to prevent memory issues
- Use session storage for temporary results

### API Optimization
- Validate parameters before expensive computations
- Stream backtest results for long-running analyses
- Implement request timeouts for custom parameter validation
- Consider parameter-based result caching

## Security Considerations

### Input Validation
- Sanitize all numeric inputs
- Validate date formats and ranges
- Prevent injection through parameter names
- Limit parameter value ranges to reasonable bounds

### Rate Limiting
- Limit backtest frequency per user/session
- Implement progressive delays for rapid parameter changes
- Monitor for abuse patterns in parameter combinations

## Testing Strategy

### Unit Testing
- Parameter validation functions
- Grid calculation with custom parameters
- API parameter parsing and validation
- Component state management

### Integration Testing
- End-to-end custom parameter workflows
- Cross-browser compatibility
- Mobile responsiveness
- Error state handling

### Performance Testing
- Backtest execution time with custom parameters
- Memory usage with large parameter sets
- Concurrent user load testing
- Cache effectiveness validation

## Migration Strategy

### Backward Compatibility
- Existing API calls continue to work unchanged
- Automatic parameter calculation remains default
- No breaking changes to existing functionality
- Gradual rollout with feature flags if needed

### Data Migration
- No database schema changes required
- Existing analysis URLs remain valid
- Parameter defaults remain unchanged
- User preferences can be migrated gradually

## Monitoring and Analytics

### Usage Metrics
- Track custom parameter usage frequency
- Monitor parameter distribution and popular ranges
- Analyze backtest success rates with custom parameters
- Measure user engagement with parameter editing features

### Performance Metrics
- Backtest execution time with custom parameters
- API response times for parameter validation
- Error rates for custom parameter submissions
- Cache hit rates for parameter-based results