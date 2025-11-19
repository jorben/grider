# Proposal: add-custom-backtest-parameters

## Problem Statement
Currently, the grid strategy parameters (price ranges, step sizes, investment amounts, etc.) are automatically calculated using ATR algorithms and cannot be customized by users. Users want the ability to manually adjust these parameters and re-run backtests with their custom settings to explore different trading scenarios and optimize their strategies.

## Proposed Solution
Add a custom parameter editor to the backtest analysis page that allows users to modify grid strategy parameters including:
- Price upper and lower limits
- Investment amount allocation
- Benchmark price
- Backtest time interval
- Grid step size
- Single trade quantity

The editor should:
1. Load current analysis parameters as defaults
2. Allow real-time parameter validation
3. Re-run backtests with custom parameters
4. Display updated results immediately

## Scope
This change affects:
- Frontend: Add parameter editor component to analysis page
- Backend: Support custom grid parameters in backtest API
- UI/UX: Integrate parameter editing into existing backtest workflow

## Benefits
- Enables users to explore different parameter combinations
- Allows strategy optimization and sensitivity analysis
- Maintains current automated behavior as default
- Provides educational value by showing parameter impact

## Risks
- Parameter validation complexity
- Potential performance impact from frequent re-runs
- User confusion with too many options
- Need to maintain backward compatibility

## Success Criteria
- Users can edit all grid strategy parameters
- Custom parameters are validated in real-time
- Backtests run successfully with custom parameters
- Results are displayed immediately
- Original automated behavior remains unchanged