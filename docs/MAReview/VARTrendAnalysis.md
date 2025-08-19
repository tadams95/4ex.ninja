:

📋 COMPREHENSIVE TASK PROMPT
Context: You are implementing the final component of Phase 2's Portfolio Correlation Management system for the 4ex.ninja trading platform. The real-time correlation calculation, breach detection, and position rebalancing are already complete and deployed to production. Now you need to implement the Correlation Trend Analysis component.

Current Status:

✅ Real-time correlation monitoring operational (60-day rolling windows)
✅ Correlation breach detection working (0.35 early warning, 0.4 breach)
✅ Dynamic position rebalancing integrated with emergency protocols
❌ MISSING: Historical correlation pattern analysis and trend prediction
Your Task: Implement a comprehensive Correlation Trend Analysis system that provides:

Historical Pattern Analysis - Identify correlation drift patterns over time
Predictive Modeling - Forecast correlation movements toward breach thresholds
Market Regime Adjustments - Adapt correlation expectations based on market conditions


🎯 SPECIFIC IMPLEMENTATION REQUIREMENTS
Backend Components to Build:
Correlation Trend Calculator

class CorrelationTrendAnalyzer:
    """
    Analyze correlation trends and predict future movements
    Target: Predict correlation breaches 1-3 days in advance
    """
    
    def calculate_correlation_trends(self, lookback_days: int = 90) -> Dict
    def predict_correlation_movement(self, pair: str, forecast_days: int = 3) -> Dict
    def detect_regime_shifts(self) -> Dict
    def generate_trend_alerts(self) -> List[Dict]

API Endpoints to Create:

/api/risk/correlation-trends - Historical trend data
/api/risk/correlation-forecast - Predictive analysis
/api/risk/correlation-regime - Market regime analysis

Frontend Components to Build:
CorrelationTrends.tsx Component

30-day correlation trend charts for each pair
Trend direction indicators (↗️ increasing, ↘️ decreasing, ➡️ stable)
Breach prediction alerts (trending toward 0.4 threshold)
Market regime indicators
Dashboard Integration

Add to RiskDashboard.tsx in the secondary grid
Replace placeholder with functional trend analysis
Real-time updates every 30 seconds

📊 TECHNICAL SPECIFICATIONS
Data Requirements:
Historical Window: 90-day correlation history for trend analysis
Prediction Horizon: 1-3 day correlation forecasts
Update Frequency: Recalculate trends every 5 minutes
Breach Threshold: Predict when correlation will exceed 0.35 (early warning)
Algorithmic Approach:
Trend Detection: Use linear regression on 30-day rolling correlations
Volatility Analysis: Calculate correlation volatility to assess stability
Regime Detection: Identify market stress periods with elevated correlations
Prediction Model: Time-series forecasting (ARIMA or exponential smoothing)
Visual Design:
Trend Charts: Line charts showing 30-day correlation trends per pair
Direction Arrows: Visual indicators for correlation direction
Prediction Zones: Shaded areas showing forecast ranges
Alert Badges: Warning indicators for pairs trending toward breach

🚀 IMPLEMENTATION STRATEGY
Phase 1: Backend Foundation (2-3 hours)
Analyze existing correlation data structure

Review current CorrelationManager implementation
Understand data storage patterns
Identify extension points for trend analysis
Implement trend calculation algorithms

Create trend detection using rolling correlation windows
Implement volatility-based stability metrics
Add prediction models for correlation forecasting
Build API endpoints

Create trend data endpoints with proper error handling
Ensure consistent data formats with existing risk APIs
Add proper authentication and rate limiting
Phase 2: Frontend Visualization (3-4 hours)
Create CorrelationTrends component

Use recharts for trend line visualization
Implement time period selectors (1W, 2W, 1M)
Add interactive tooltips and hover states
Integrate prediction indicators

Visual alerts for pairs trending toward breach
Color-coded trend directions
Confidence intervals for predictions
Dashboard integration

Replace placeholder in RiskDashboard
Ensure responsive layout consistency
Test real-time update integration
Phase 3: Validation & Polish (1-2 hours)
Test prediction accuracy

Validate against recent historical data
Adjust model parameters for optimal performance
Document prediction confidence levels
Error handling and edge cases

Handle missing data gracefully
Manage API failures with fallback states
Ensure smooth user experience during updates


✅ SUCCESS CRITERIA
Technical Validation:

 Correlation trends calculated accurately for all major pairs
 Prediction model shows >70% accuracy for 1-day forecasts
 API endpoints respond within 200ms average
 Frontend component updates smoothly every 30 seconds
 Zero critical errors in production deployment
Business Impact:

 Early warning system predicts correlation breaches 1-2 days ahead
 Trend analysis helps optimize position sizing decisions
 Market regime detection improves correlation threshold management
 Dashboard provides actionable correlation intelligence
User Experience:

 Correlation trends are visually clear and intuitive
 Prediction alerts are actionable and not overwhelming
 Component integrates seamlessly with existing dashboard
 Mobile responsiveness maintained across all screen sizes

  SPECIFIC TECHNICAL TASKS
Extend CorrelationManager class with trend analysis methods
Create correlation_trends.py module for advanced analytics
Add database tables for storing historical trend data
Build CorrelationTrends.tsx with recharts integration
Update RiskDashboard.tsx to include trends component
Create useCorrelationTrends.ts hook for data management
Add proper TypeScript types for trend data structures
Write unit tests for trend calculation algorithms
Document API endpoints and component usage
Deploy and validate in production environment