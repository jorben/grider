# Implementation Tasks for add-custom-backtest-parameters

## Frontend Tasks

### 1. Create Grid Parameter Editor Component
- [x] Create `GridParameterEditor.jsx` component
- [x] Include form fields for all grid parameters (price limits, investment amount, benchmark price, grid step size, single trade quantity)
- [x] Add real-time parameter validation
- [x] Load current analysis parameters as defaults
- [x] Integrate with existing backtest workflow

### 2. Add Time Interval Selector
- [x] Add date range picker for backtest time interval
- [x] Validate date ranges against available data
- [x] Update backtest API calls to include custom time ranges

### 3. Update Analysis Page Layout
- [x] Add parameter editor section to analysis page
- [x] Ensure responsive design for mobile/desktop
- [x] Add toggle to show/hide parameter editor
- [x] Position editor near backtest results

### 4. Parameter Validation and Error Handling
- [x] Implement client-side parameter validation
- [x] Show validation errors in real-time
- [x] Prevent invalid parameter combinations
- [x] Add helpful error messages and suggestions

### 5. Integration with Backtest Tab
- [x] Modify `BacktestTab.jsx` to accept custom grid parameters
- [x] Update parameter change handlers
- [x] Ensure parameter changes trigger re-backtest
- [x] Maintain backward compatibility

## Backend Tasks

### 6. Update Backtest API to Accept Custom Grid Parameters
- [x] Modify `/api/backtest` endpoint to accept custom grid strategy parameters
- [x] Add parameter validation in backend
- [x] Support custom time intervals in data fetching
- [x] Return validation errors for invalid parameters

### 7. Update Grid Strategy Calculation Logic
- [x] Modify `BacktestEngine` to use custom parameters when provided
- [x] Maintain automatic calculation as fallback
- [x] Add parameter validation before backtest execution
- [x] Ensure custom parameters override automatic calculations

### 8. Add Custom Parameter Support to Grid Algorithms
- [x] Update `ArithmeticGridCalculator` to accept custom parameters
- [x] Modify grid level calculation to use provided parameters
- [x] Add validation for custom parameter combinations
- [x] Maintain existing automatic calculation methods

## Testing Tasks

### 9. Unit Tests for Parameter Validation
- Test parameter validation logic
- Test edge cases and invalid inputs
- Test parameter combinations
- Ensure backward compatibility

### 10. Integration Tests for Custom Backtests
- Test end-to-end custom parameter flow
- Test backtest results with custom parameters
- Test time interval filtering
- Test error handling and validation

### 11. UI/UX Testing
- Test parameter editor on different screen sizes
- Test parameter validation feedback
- Test backtest re-run functionality
- Test loading states and error handling

## Documentation Tasks

### 12. Update User Documentation
- Add documentation for custom parameter feature
- Include parameter explanations and best practices
- Add examples of parameter optimization
- Update FAQ and troubleshooting guides

### 13. Update API Documentation
- Document new API parameters for custom backtest
- Update endpoint specifications
- Add parameter validation rules
- Include example requests/responses