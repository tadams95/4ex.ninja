# 📖 Backtest Page API Documentation
## Quick Reference for Frontend Integration

**Base URL**: `/api/v1/backtest/page`  
**Authentication**: None required  
**Response Format**: JSON with `status`, `data`, and `timestamp` fields

---

## 📊 Available Endpoints

### 1. **Performance Data**
```
GET /api/v1/backtest/page/performance
```
**Purpose**: Get top 10 strategy performance metrics  
**Response Size**: ~15KB  
**Cache TTL**: 1 hour

**Response Structure:**
```json
{
  "status": "success",
  "data": {
    "extraction_date": "2025-08-19",
    "total_strategies_analyzed": 276,
    "top_performing_strategies": [
      {
        "rank": 1,
        "currency_pair": "EUR_USD",
        "strategy": "conservative_conservative_weekly",
        "performance_metrics": {
          "annual_return": 0.156,
          "annual_return_pct": "15.6%",
          "sharpe_ratio": 2.08,
          "max_drawdown": 0.048,
          "max_drawdown_pct": "4.8%",
          "win_rate": 0.59,
          "win_rate_pct": "59.0%"
        }
      }
    ]
  }
}
```

### 2. **Visual Datasets (All)**
```
GET /api/v1/backtest/page/visual-datasets
```
**Purpose**: Get all chart datasets in single request  
**Response Size**: ~25KB  
**Cache TTL**: 1 hour

**Available Datasets:**
- `monthly_heatmap` - Calendar heatmap data
- `drawdown_analysis` - Risk visualization data
- `win_rate_analysis` - Success rate patterns  
- `risk_return_scatter` - Strategy positioning
- `comparison_matrix` - Head-to-head metrics

### 3. **Visual Datasets (Individual)**
```
GET /api/v1/backtest/page/visual-datasets/{dataset_name}
```
**Purpose**: Get specific chart dataset  
**Parameters**: `monthly_heatmap`, `drawdown_analysis`, `win_rate_analysis`, `risk_return_scatter`, `comparison_matrix`  
**Response Size**: ~5KB per dataset  
**Cache TTL**: 1 hour

**Example Usage:**
```javascript
// Load risk vs return scatter plot data
const response = await fetch('/api/v1/backtest/page/visual-datasets/risk_return_scatter');
const { data } = await response.json();
// data.data contains array of strategy points with risk/return coordinates
```

### 4. **Methodology Content**
```
GET /api/v1/backtest/page/methodology
```
**Purpose**: Get strategy documentation and educational content  
**Response Size**: ~22KB  
**Cache TTL**: 6 hours

**Response Structure:**
```json
{
  "status": "success", 
  "data": {
    "strategy_methodology": "# Complete strategy explanation markdown...",
    "performance_attribution": "# Return source analysis markdown...",
    "last_updated": "2025-08-19T03:39:02.675422Z"
  }
}
```

### 5. **Equity Curves**
```
GET /api/v1/backtest/page/equity-curves
```
**Purpose**: Get 5-year equity progression data for charts  
**Response Size**: ~12KB  
**Cache TTL**: 1 hour

**Chart Data Structure:**
```json
{
  "data": {
    "equity_curves": {
      "EUR_USD_conservative_conservative_weekly": {
        "dates": ["2020-01-01", "2020-01-08", ...],
        "equity_values": [100000, 100234, ...],
        "final_equity": 192019.35,
        "total_return": 0.92
      }
    }
  }
}
```

### 6. **Summary (Hero Section)**
```
GET /api/v1/backtest/page/summary
```
**Purpose**: Get key metrics for hero section  
**Response Size**: ~3KB  
**Cache TTL**: 30 minutes

**Response Structure:**
```json
{
  "data": {
    "hero_metrics": {
      "top_annual_return": "15.6%",
      "top_sharpe_ratio": 2.08,
      "max_drawdown": "4.8%", 
      "win_rate": "59.0%",
      "strategies_analyzed": 276,
      "data_period": "5 Years (2020-2025)"
    },
    "top_3_strategies": [ /* top 3 strategy objects */ ]
  }
}
```

---

## 🔧 Frontend Integration Examples

### **React Query Setup**
```typescript
import { useQuery } from '@tanstack/react-query';

const useBacktestPerformance = () => {
  return useQuery({
    queryKey: ['backtest', 'performance'],
    queryFn: async () => {
      const response = await fetch('/api/v1/backtest/page/performance');
      if (!response.ok) throw new Error('Failed to fetch performance data');
      return response.json();
    },
    staleTime: 1000 * 60 * 60, // 1 hour
  });
};
```

### **Chart.js Integration**
```typescript
// Monthly heatmap chart
const { data: visualData } = useQuery({
  queryKey: ['backtest', 'visual', 'monthly_heatmap'],
  queryFn: () => fetch('/api/v1/backtest/page/visual-datasets/monthly_heatmap').then(r => r.json())
});

const chartConfig = {
  type: 'bar',
  data: {
    labels: visualData?.data?.data?.[strategyKey]?.months || [],
    datasets: [{
      label: 'Monthly Returns (%)',
      data: visualData?.data?.data?.[strategyKey]?.returns || [],
      backgroundColor: 'rgba(34, 197, 94, 0.8)'
    }]
  }
};
```

### **Bulk Data Loading**
```typescript
const useBacktestPageData = () => {
  return useQuery({
    queryKey: ['backtest', 'page', 'all'],
    queryFn: async () => {
      const [performance, visuals, summary] = await Promise.all([
        fetch('/api/v1/backtest/page/performance').then(r => r.json()),
        fetch('/api/v1/backtest/page/visual-datasets').then(r => r.json()),
        fetch('/api/v1/backtest/page/summary').then(r => r.json())
      ]);
      
      return {
        performance: performance.data,
        visuals: visuals.data,
        summary: summary.data
      };
    },
    staleTime: 1000 * 60 * 30, // 30 minutes
  });
};
```

---

## ⚠️ Error Handling

### **HTTP Status Codes**
- `200` - Success
- `404` - Data file not found
- `500` - Server error (JSON parsing, file system issues)

### **Error Response Format**
```json
{
  "detail": "Performance data not found",
  "status_code": 404
}
```

### **Frontend Error Handling**
```typescript
const { data, error, isLoading } = useBacktestPerformance();

if (error) {
  return <div>Error loading backtest data: {error.message}</div>;
}

if (isLoading) {
  return <div>Loading backtest performance...</div>;
}
```

---

## 🚀 Performance Tips

### **Optimization Strategies**
1. **Use summary endpoint** for hero section (fastest)
2. **Load individual datasets** for specific charts (lazy loading)
3. **Cache methodology content** (changes infrequently)
4. **Batch visual datasets** for dashboard initialization

### **Caching Headers**
```javascript
// Add cache headers for production
fetch('/api/v1/backtest/page/performance', {
  headers: {
    'Cache-Control': 'max-age=3600' // 1 hour
  }
});
```

---

## 📱 Mobile Considerations

### **Response Size Management**
- **Summary endpoint**: Use for mobile hero sections (3KB)
- **Individual datasets**: Load specific charts on demand
- **Methodology**: Consider pagination or accordion display
- **Equity curves**: Sample data points for mobile charts

### **Progressive Loading**
```typescript
// Load critical data first, then enhance
const { data: summary } = useQuery(['backtest', 'summary'], ...);
const { data: details } = useQuery(['backtest', 'performance'], ..., {
  enabled: !!summary // Load after summary
});
```

---

**API Ready**: All endpoints tested and production-ready for immediate frontend integration!
