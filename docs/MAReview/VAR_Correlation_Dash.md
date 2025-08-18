# 📊 VaR & Correlation Dashboard Implementation Guide
## Phase 2 Dashboard Development - Bite-Sized Task Breakdown

**Created:** August 17, 2025  
**Parent Document:** [PHASE2_VAR_CORRELATION_IMPLEMENTATION_PLAN.md](./PHASE2_VAR_CORRELATION_IMPLEMENTATION_PLAN.md)  
**Target Completion:** September 7, 2025 (3 weeks)  
**Current Focus:** Week 3 Dashboard & Alert Implementation

---

## 🎯 **Overview**

This document breaks down the remaining Phase 2 objectives into manageable, bite-sized tasks:

1. **Risk Dashboard Framework** (Frontend visualization)
2. **Alert Management System** (Automated notification system)  
3. **Correlation Trend Analysis** (Historical pattern analysis)

Each task is designed to be completed in 2-5 hours and can be tested independently.

---

## 🧩 **Bite-Sized Task Breakdown**

### **🎯 SPRINT 1: Basic Dashboard Foundation (Days 1-3)**

#### **Task 1.1: Backend API Endpoints** *(2-3 hours)* ✅ **COMPLETED**
**Priority:** 🔥 CRITICAL PATH  
**Dependencies:** None

- ✅ Create `/api/risk/var-summary` endpoint
  - Return current portfolio VaR for all methods (Historical, Parametric, Monte Carlo)
  - Include target vs actual comparison (0.31% target)
  - Add timestamp and confidence level
- ✅ Create `/api/risk/correlation-matrix` endpoint  
  - Return real-time correlation matrix for all active pairs
  - Include correlation strength indicators
  - Add breach status for each pair (threshold: 0.4)
- ✅ Test endpoints return proper JSON structure
- ✅ Add basic error handling and validation

**Implementation Notes:**
- Created `src/api/routes/risk.py` with three working endpoints
- Integrated with Phase 2 VaRMonitor and CorrelationManager 
- All endpoints tested and validated with real calculations
- Mock portfolio state handles development mode properly

**Expected Output:**
```json
// /api/risk/var-summary
{
  "current_var": {
    "historical": 0.0029,
    "parametric": 0.0031,
    "monte_carlo": 0.0028
  },
  "target": 0.0031,
  "confidence_level": 0.95,
  "timestamp": "2025-08-17T10:30:00Z",
  "status": "within_target"
}

// /api/risk/correlation-matrix
{
  "correlation_matrix": {
    "EUR_USD": {"GBP_USD": 0.34, "AUD_USD": 0.28, ...},
    "GBP_USD": {"EUR_USD": 0.34, "AUD_USD": 0.31, ...}
  },
  "breach_alerts": ["EUR_USD-GBP_USD: 0.34"],
  "timestamp": "2025-08-17T10:30:00Z"
}
```

#### **Task 1.2: Frontend Dashboard Shell** *(2-3 hours)*
**Priority:** 🔥 CRITICAL PATH  
**Dependencies:** Task 1.1

- [ ] Create `RiskDashboard.tsx` component in `/src/components/dashboard/`
- [ ] Add basic layout with placeholder cards using Tailwind CSS
- [ ] Set up routing to dashboard page (`/dashboard/risk`)
- [ ] Test component renders without errors
- [ ] Add basic navigation breadcrumbs

**Component Structure:**
```tsx
// src/components/dashboard/RiskDashboard.tsx
export default function RiskDashboard() {
  return (
    <div className="p-6 space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* VaR Display Card */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">Portfolio VaR</h3>
          {/* Placeholder */}
        </div>
        
        {/* Correlation Heatmap Card */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">Correlation Matrix</h3>
          {/* Placeholder */}
        </div>
      </div>
    </div>
  );
}
```

#### **Task 1.3: Real-Time VaR Display Component** *(3-4 hours)*
**Priority:** 🔥 CRITICAL PATH  
**Dependencies:** Tasks 1.1, 1.2

- [ ] Create `VaRDisplay.tsx` component
- [ ] Connect to backend VaR endpoint using React Query/SWR
- [ ] Display current VaR vs 0.31% target with progress indicators
- [ ] Add simple progress bar visualization (red > target, green < target)
- [ ] Test with mock data first, then live data
- [ ] Add auto-refresh every 30 seconds

**Component Features:**
- Current VaR value with color coding
- Target comparison (0.31%)
- Multi-method VaR display (Historical, Parametric, Monte Carlo)
- Status indicator (Within Target / Breach Alert)
- Last updated timestamp

---

### **🎯 SPRINT 2: Core Visualizations (Days 4-6)**

#### **Task 2.1: Correlation Heat Map** *(4-5 hours)*
**Priority:** 🔥 CRITICAL PATH  
**Dependencies:** Task 1.1

- [ ] Install visualization library: `npm install react-heatmap-grid`
- [ ] Create `CorrelationHeatMap.tsx` component
- [ ] Connect to correlation matrix API
- [ ] Add color coding:
  - 🔴 Red: > 0.4 (breach)
  - 🟡 Yellow: 0.3-0.4 (warning)
  - 🟢 Green: < 0.3 (safe)
- [ ] Test with sample correlation data
- [ ] Add hover tooltips with exact correlation values

**Visualization Requirements:**
- Symmetric correlation matrix
- Currency pair labels
- Interactive hover states
- Responsive design for mobile

#### **Task 2.2: VaR Trend Chart** *(3-4 hours)*
**Priority:** 🚀 HIGH PRIORITY  
**Dependencies:** Task 1.1

- [ ] Install charting library: `npm install recharts`
- [ ] Create `VaRTrendChart.tsx` component
- [ ] Display 1D, 1W, 1M time periods with toggle buttons
- [ ] Show VaR trend vs target line (0.31%)
- [ ] Add toggle buttons for time periods
- [ ] Test with historical VaR data from backend

**Chart Features:**
- Line chart with time-series data
- Target line at 0.31%
- Time period selector (1D/1W/1M)
- Breach highlighting (red areas above target)

#### **Task 2.3: Dashboard Layout Integration** *(2 hours)*
**Priority:** 🚀 HIGH PRIORITY  
**Dependencies:** Tasks 1.3, 2.1, 2.2

- [ ] Integrate VaR display into dashboard grid
- [ ] Integrate correlation heatmap
- [ ] Add responsive grid layout for mobile/tablet/desktop
- [ ] Test on different screen sizes
- [ ] Optimize layout spacing and visual hierarchy

---

### **🎯 SPRINT 3: Alert Management System (Days 7-9)**

#### **Task 3.1: Alert Data Models** *(2 hours)*
**Priority:** 🚀 HIGH PRIORITY  
**Dependencies:** None

- [ ] Create alert database schema in backend
- [ ] Create alert TypeScript interfaces for frontend
- [ ] Add alert priority levels: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`
- [ ] Test database migrations
- [ ] Document alert data structure

**Alert Schema:**
```typescript
interface RiskAlert {
  id: string;
  type: 'var_breach' | 'correlation_breach' | 'emergency';
  priority: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  message: string;
  details: Record<string, any>;
  timestamp: string;
  acknowledged: boolean;
  resolved: boolean;
}
```

#### **Task 3.2: Backend Alert Endpoints** *(3-4 hours)*
**Priority:** 🚀 HIGH PRIORITY  
**Dependencies:** Task 3.1

- [ ] Create `/api/alerts/active` endpoint (unresolved alerts)
- [ ] Create `/api/alerts/history` endpoint (resolved alerts with pagination)
- [ ] Create `/api/alerts/acknowledge` endpoint (mark as acknowledged)
- [ ] Add alert generation logic for VaR breaches (when VaR > 0.31%)
- [ ] Test alert creation and retrieval with sample data

**Endpoint Specifications:**
- GET `/api/alerts/active` - Returns active alerts sorted by priority
- GET `/api/alerts/history?page=1&limit=50` - Returns historical alerts
- POST `/api/alerts/{alertId}/acknowledge` - Acknowledges an alert

#### **Task 3.3: Alert Display Component** *(3-4 hours)*
**Priority:** 🚀 HIGH PRIORITY  
**Dependencies:** Task 3.2

- [ ] Create `AlertPanel.tsx` component
- [ ] Display active alerts with priority colors and icons
- [ ] Add acknowledge/dismiss functionality
- [ ] Add alert history view with pagination
- [ ] Test alert interactions (acknowledge, view details)

**Alert Panel Features:**
- Priority color coding (Red=Critical, Orange=High, Yellow=Medium, Blue=Low)
- Alert timestamp and message
- Quick acknowledge button
- Expandable alert details
- Alert history toggle

#### **Task 3.4: Real-Time Alert Updates** *(2-3 hours)*
**Priority:** 📈 MEDIUM PRIORITY  
**Dependencies:** Task 3.3

- [ ] Set up WebSocket connection for live alerts
- [ ] Add browser notifications for new alerts
- [ ] Test real-time alert delivery
- [ ] Add alert sound/visual indicators (optional)
- [ ] Implement alert rate limiting to prevent spam

---

### **🎯 SPRINT 4: Advanced Features (Days 10-12)**

#### **Task 4.1: Correlation Trend Analysis** *(4-5 hours)*
**Priority:** 📈 MEDIUM PRIORITY  
**Dependencies:** Task 2.1

- [ ] Create correlation trend calculation in backend
- [ ] Add `/api/risk/correlation-trends` endpoint
- [ ] Create `CorrelationTrends.tsx` component
- [ ] Display correlation drift over time (30-day rolling trends)
- [ ] Add prediction indicators based on trend analysis

**Features:**
- 30-day correlation trend for each pair
- Trend direction indicators (↗️ increasing, ↘️ decreasing, ➡️ stable)
- Breach prediction alerts (trending toward 0.4 threshold)

#### **Task 4.2: Portfolio Health Scoring** *(3-4 hours)*
**Priority:** 📈 MEDIUM PRIORITY  
**Dependencies:** Tasks 1.3, 2.1

- [ ] Implement portfolio health algorithm in backend
- [ ] Create `/api/risk/portfolio-health` endpoint
- [ ] Create `PortfolioHealth.tsx` component
- [ ] Display overall risk score (0-100 scale)
- [ ] Add health trend indicators and contributing factors

**Health Score Calculation:**
- VaR compliance (40% weight)
- Correlation levels (30% weight)
- Alert frequency (20% weight)
- Emergency protocol status (10% weight)

#### **Task 4.3: Risk Metrics Integration** *(2-3 hours)*
**Priority:** 📈 MEDIUM PRIORITY  
**Dependencies:** Task 4.2

- [ ] Connect emergency risk status to dashboard
- [ ] Add risk-adjusted performance metrics display
- [ ] Create unified risk summary view
- [ ] Test all metrics display correctly
- [ ] Add export functionality for risk reports

---

### **🎯 SPRINT 5: Polish & Testing (Days 13-15)**

#### **Task 5.1: Dashboard Polish** *(2-3 hours)*
**Priority:** ✨ LOW PRIORITY  
**Dependencies:** All previous tasks

- [ ] Add loading states for all components (skeleton loaders)
- [ ] Improve error handling and user feedback
- [ ] Add tooltips and help text for complex metrics
- [ ] Optimize dashboard performance (lazy loading, memoization)
- [ ] Add dark mode support (optional)

#### **Task 5.2: Alert System Refinement** *(2-3 hours)*
**Priority:** ✨ LOW PRIORITY  
**Dependencies:** Task 3.4

- [ ] Fine-tune alert thresholds based on testing
- [ ] Add alert escalation logic (auto-escalate unacknowledged critical alerts)
- [ ] Implement alert rate limiting and deduplication
- [ ] Test false positive rates and adjust sensitivity

#### **Task 5.3: End-to-End Testing** *(3-4 hours)*
**Priority:** ✨ LOW PRIORITY  
**Dependencies:** All tasks

- [ ] Create dashboard integration tests using Playwright
- [ ] Test alert workflow end-to-end
- [ ] Validate all risk calculations match backend
- [ ] Performance testing under load (stress test)
- [ ] Cross-browser testing

#### **Task 5.4: Documentation** *(2 hours)*
**Priority:** ✨ LOW PRIORITY  
**Dependencies:** All tasks

- [ ] Document dashboard user guide with screenshots
- [ ] Create alert management documentation
- [ ] Update API documentation with new endpoints
- [ ] Finalize Phase 2 completion report

---

## 📊 **Task Priority Matrix**

### **🔥 CRITICAL PATH (Must Complete First)**
1. **Task 1.1:** Backend API Endpoints
2. **Task 1.2:** Frontend Dashboard Shell
3. **Task 1.3:** Real-Time VaR Display
4. **Task 2.1:** Correlation Heat Map

### **🚀 HIGH PRIORITY (Core Features)**
5. **Task 3.2:** Backend Alert Endpoints
6. **Task 3.3:** Alert Display Component
7. **Task 2.2:** VaR Trend Chart
8. **Task 3.4:** Real-Time Alert Updates

### **📈 MEDIUM PRIORITY (Enhancement)**
9. **Task 4.1:** Correlation Trend Analysis
10. **Task 4.2:** Portfolio Health Scoring
11. **Task 5.1:** Dashboard Polish

### **✨ LOW PRIORITY (Final Polish)**
12. **Task 5.2:** Alert System Refinement
13. **Task 5.3:** End-to-End Testing
14. **Task 5.4:** Documentation

---

## 🔄 **Daily Sprint Structure**

### **Day 1: Foundation Setup**
- **Morning (3-4 hours):** Task 1.1 - Backend API Endpoints
- **Afternoon (2-3 hours):** Task 1.2 - Dashboard Shell

### **Day 2: Core VaR Display**
- **Morning (3-4 hours):** Task 1.3 - VaR Display Component
- **Afternoon (2-3 hours):** Start Task 2.1 - Correlation HeatMap setup

### **Day 3: Correlation Visualization**
- **Morning (2-3 hours):** Finish Task 2.1 - Correlation HeatMap
- **Afternoon (3-4 hours):** Task 2.2 - VaR Trend Chart

### **Day 4: Layout Integration**
- **Morning (2 hours):** Task 2.3 - Dashboard Layout Integration
- **Afternoon (3-4 hours):** Task 3.1 & 3.2 - Alert System Backend

### **Day 5: Alert UI Development**
- **Morning (3-4 hours):** Task 3.3 - Alert Display Component
- **Afternoon (2-3 hours):** Task 3.4 - Real-Time Alerts

### **Days 6-8: Advanced Features**
- Task 4.1: Correlation Trends
- Task 4.2: Portfolio Health
- Task 4.3: Risk Metrics Integration

### **Days 9-11: Polish & Testing**
- Task 5.1: Dashboard Polish
- Task 5.2: Alert Refinement
- Task 5.3: End-to-End Testing
- Task 5.4: Documentation

---

## ✅ **Definition of Done**

Each task is considered complete when it meets these criteria:

### **Functional Requirements**
- [ ] Feature works as specified
- [ ] Integrates properly with existing system
- [ ] Handles error cases gracefully
- [ ] Responsive design (mobile/tablet/desktop)

### **Code Quality**
- [ ] TypeScript types defined
- [ ] Unit tests written (for backend endpoints)
- [ ] Code follows project conventions
- [ ] Inline documentation added

### **Testing**
- [ ] Manual testing completed
- [ ] Integration testing passed
- [ ] No console errors or warnings
- [ ] Performance acceptable (<2s load time)

### **Documentation**
- [ ] API endpoints documented (if applicable)
- [ ] Component usage documented
- [ ] Any configuration changes noted

---

## 🚀 **Getting Started Checklist**

Before starting development:

### **Environment Setup**
- [ ] Backend server running (`python3 -m uvicorn src.app:app --reload`)
- [ ] Frontend development server running (`npm run dev`)
- [ ] Database connected and Phase 2 VaR/Correlation systems active
- [ ] API endpoints accessible at `http://localhost:8000/api/`

### **Development Tools**
- [ ] Install required npm packages:
  ```bash
  npm install react-heatmap-grid recharts @tanstack/react-query
  ```
- [ ] VS Code extensions: Tailwind CSS IntelliSense, TypeScript
- [ ] Browser dev tools setup for testing

### **Code Organization**
```
4ex.ninja-frontend/src/
├── components/
│   └── dashboard/
│       ├── RiskDashboard.tsx
│       ├── VaRDisplay.tsx
│       ├── CorrelationHeatMap.tsx
│       ├── VaRTrendChart.tsx
│       ├── AlertPanel.tsx
│       └── PortfolioHealth.tsx
├── hooks/
│   ├── useVaRData.ts
│   ├── useCorrelationData.ts
│   └── useAlerts.ts
└── types/
    └── risk.ts
```

---

## 🎯 **Success Metrics**

### **Technical Validation**
- [ ] All 14 tasks completed successfully
- [ ] Dashboard loads in <2 seconds
- [ ] Real-time updates work within 30 seconds
- [ ] Zero critical bugs in production
- [ ] All API endpoints return proper responses

### **User Experience**
- [ ] Dashboard is intuitive and easy to navigate
- [ ] VaR and correlation data clearly displayed
- [ ] Alerts are actionable and not overwhelming
- [ ] Mobile responsiveness maintained

### **Business Impact**
- [ ] VaR monitoring operational (0.31% target visible)
- [ ] Correlation management functional (<0.4 threshold monitoring)
- [ ] Risk transparency increased through visualization
- [ ] Foundation ready for Phase 3 implementation

---

## 📋 **Task Tracking Template**

Use this template to track progress on each task:

```markdown
## Task X.X: [Task Name]
**Status:** 🔄 In Progress / ✅ Complete / ❌ Blocked  
**Assigned:** [Developer Name]  
**Started:** [Date]  
**Completed:** [Date]  
**Time Spent:** [Actual Hours]

### Progress Notes:
- [ ] Subtask 1
- [ ] Subtask 2
- [ ] Subtask 3

### Blockers/Issues:
- [Any blockers or issues encountered]

### Testing Results:
- [Testing outcomes and any bugs found]

### Code Review:
- **Reviewer:** [Name]
- **Status:** Pending/Approved
- **Comments:** [Any review feedback]
```

---

**🚀 Ready to Start Dashboard Implementation! 🚀**

**Next Step:** Begin with Task 1.1 - Backend API Endpoints
