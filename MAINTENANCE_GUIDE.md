# 🛡️ Threat Modeling Pipeline - Maintenance Guide

## Defensive Programming & Architecture Maintenance

### **Overview**
The Threat Modeling Pipeline is built with enterprise-grade defensive programming practices. This guide covers maintaining the robust, error-resistant architecture that prevents failures and ensures reliable operation.

---

## 🔧 **Key Defensive Programming Implementations**

### **1. Comprehensive Input Validation**

**Location**: Throughout application (API endpoints, UI components, database models)

**Implementation**:
```python
# API Validation Example (apps/api/app/api/endpoints/agent_management.py)
@router.get("/{agent_name}/history")
async def get_agent_execution_history(
    agent_name: str,
    limit: int = Query(20, ge=1, le=100),  # Defensive: Limit result size
    db: AsyncSession = Depends(get_db)
):
    try:
        # Verify agent exists before querying
        agent = agent_registry.get_agent(agent_name)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent {agent_name} not found")
        
        # Additional validation logic...
    except Exception as e:
        logger.error(f"Failed to get execution history for {agent_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get execution history: {e}")
```

**Maintenance Tasks**:
- **Monthly**: Review validation logic in new endpoints
- **Quarterly**: Audit input sanitization across all forms
- **When Adding Features**: Ensure all new inputs have validation

### **2. Timeout & Error Handling**

**Location**: API calls, WebSocket connections, database operations

**Implementation**:
```typescript
// Frontend Timeout Example (apps/web/lib/api.ts)
async function getAvailableAgents(): Promise<AgentInfo[]> {
  try {
    // Defensive: Add timeout to prevent hanging requests
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 30000)
    
    const response = await fetch(`${API_URL}/api/agents/list`, {
      signal: controller.signal
    })
    
    clearTimeout(timeoutId)
    // Validation and error handling...
  } catch (error) {
    if (error.name === 'AbortError') {
      throw new Error('Request timed out. Please check your connection and try again.')
    }
    throw new Error(`Unable to load agents: ${error.message}`)
  }
}
```

**Maintenance Tasks**:
- **Weekly**: Monitor timeout logs for patterns
- **Monthly**: Review timeout values against usage patterns
- **When Performance Issues**: Adjust timeouts based on monitoring data

### **3. Graceful Degradation**

**Location**: Task API, WebSocket connections, agent availability

**Implementation**:
```python
# Graceful Degradation Example (apps/api/app/api/endpoints/tasks.py)
@router.get("/list")
async def list_active_tasks():
    try:
        result = await asyncio.wait_for(get_tasks_with_timeout(), timeout=3.0)
        return result
    except asyncio.TimeoutError:
        # Return empty result instead of error to prevent UI issues
        return {
            "active": {},
            "warning": "Query timed out, workers may be slow"
        }
    except Exception as e:
        # Return empty result instead of error to prevent UI issues  
        return {
            "active": {},
            "error": "Failed to query task status"
        }
```

**Maintenance Tasks**:
- **Weekly**: Check fallback mechanisms are working
- **Monthly**: Review degraded state handling
- **During Outages**: Verify graceful degradation prevents cascading failures

---

## 🎯 **Performance Optimization Maintenance**

### **Slow Endpoint Monitoring**

**Critical Endpoints to Monitor**:
1. `/api/tasks/list` - Optimized with 3-second timeout
2. `/api/agents/list` - Should respond in <100ms
3. `/api/agents/{name}/history` - May need restart for new endpoints

**Monthly Performance Review**:
```bash
# Check endpoint response times
curl -w "@curl-format.txt" -s -o /dev/null http://localhost/api/agents/list
curl -w "@curl-format.txt" -s -o /dev/null http://localhost/api/tasks/list
```

Create `curl-format.txt`:
```
     time_namelookup:  %{time_namelookup}s\n
        time_connect:  %{time_connect}s\n
     time_appconnect:  %{time_appconnect}s\n
    time_pretransfer:  %{time_pretransfer}s\n
       time_redirect:  %{time_redirect}s\n
  time_starttransfer:  %{time_starttransfer}s\n
                     ----------\n
          time_total:  %{time_total}s\n
```

### **Database Connection Health**

**Monthly Check**:
```python
# Run this in apps/api/ environment
from app.database import engine
import asyncio

async def check_connection_health():
    async with engine.begin() as conn:
        result = await conn.execute("SELECT 1")
        print("✅ Database connection healthy")
        
        # Check connection pool
        pool = engine.pool
        print(f"Pool size: {pool.size()}")
        print(f"Checked out: {pool.checkedout()}")
        print(f"Overflow: {pool.overflow()}")
        print(f"Invalid: {pool.invalid()}")

asyncio.run(check_connection_health())
```

### **Asyncpg Connection Pool Recovery**

**Issue**: "another operation is in progress" errors with asyncpg

**Immediate Recovery**:
```bash
# Quick restart to clear connection pool
docker-compose restart api

# Re-initialize RBAC if authentication fails
docker-compose exec api python -m app.core.init_rbac
```

**Robust Connection Manager** (implemented in `/app/core/db_connection_manager.py`):
- Uses NullPool to avoid asyncpg pooling issues
- Automatic fallback to direct asyncpg connections
- Connection reinitialization on failure
- Multiple retry strategies

**Monthly Connection Pool Health Check**:
```bash
# Check for connection pool errors in logs
docker-compose logs api | grep -E "another operation|Event loop|InterfaceError" | tail -20

# Monitor connection pool metrics
curl http://localhost:8000/health | jq '.database'
```

---

## 🚨 **Error Monitoring & Response**

### **Log Analysis**

**Weekly Log Review**:
```bash
# Check for defensive programming catches
cd /path/to/project
grep -r "Failed to" apps/api/logs/ | head -20
grep -r "Timeout" apps/api/logs/ | head -20  
grep -r "Defensive:" apps/api/logs/ | head -20
```

### **Common Issues & Solutions**

| Issue | Symptoms | Solution | Prevention |
|-------|----------|----------|------------|
| **Slow Tasks API** | `/api/tasks/list` >3s | Check Celery workers | Monitor worker health weekly |
| **Agent List 404** | Frontend can't load agents | Restart API server | Implement health checks |
| **WebSocket Drops** | Progress tracking fails | Check connection limits | Monitor connection pool |
| **Timeout Errors** | 5-minute threat generation timeout | Check agent performance | Monitor execution times |

### **Health Check Automation**

**Daily Automated Checks** (Add to cron):
```bash
#!/bin/bash
# health-check.sh
API_URL="http://localhost:8000"

# Check core endpoints
curl -f "$API_URL/health" || echo "❌ Health check failed"
curl -f "$API_URL/api/agents/list" || echo "❌ Agent list failed"
curl -f "$API_URL/api/tasks/list" || echo "❌ Tasks list failed"

# Check response times
RESPONSE_TIME=$(curl -w "%{time_total}" -s -o /dev/null "$API_URL/api/agents/list")
if (( $(echo "$RESPONSE_TIME > 1.0" | bc -l) )); then
    echo "⚠️ Agent list slow: ${RESPONSE_TIME}s"
fi
```

---

## 🔄 **Future Improvements & Expansion**

### **Enhanced Defensive Programming**

**Next Quarter Improvements**:
1. **Circuit Breaker Pattern**: Implement across all external service calls
2. **Rate Limiting**: Add per-user API rate limits  
3. **Retry Logic**: Exponential backoff for failed operations
4. **Health Checks**: Comprehensive service health monitoring
5. **Alerting**: Automated alerts for degraded performance

### **Monitoring & Observability**

**Recommended Additions**:
```python
# Add to requirements.txt
prometheus-client==0.16.0
structlog==23.1.0
```

**Implementation Plan**:
1. **Metrics Collection**: Request duration, error rates, queue depths
2. **Structured Logging**: JSON logs with correlation IDs
3. **Alerting Rules**: Automated notifications for issues
4. **Dashboard**: Grafana dashboard for real-time monitoring

### **Scalability Improvements**

**As Usage Grows**:
1. **Database Connection Pooling**: Increase pool size based on load
2. **Celery Worker Scaling**: Add workers during peak usage
3. **Caching Layer**: Redis caching for frequently accessed data
4. **Load Balancing**: Multiple API instances behind load balancer

---

## 🛠️ **Maintenance Schedule**

### **Daily (Automated)**
- [ ] Health check endpoint verification
- [ ] Response time monitoring
- [ ] Error log review (automated alerts)

### **Weekly**
- [ ] Review timeout patterns in logs
- [ ] Check WebSocket connection stability  
- [ ] Verify graceful degradation mechanisms
- [ ] Monitor Celery worker performance

### **Monthly**
- [ ] Performance baseline review
- [ ] Database connection pool analysis
- [ ] Input validation audit for new features
- [ ] Update timeout values based on usage patterns

### **Quarterly**
- [ ] Comprehensive security review
- [ ] Defensive programming pattern analysis
- [ ] Capacity planning and scaling assessment
- [ ] Update monitoring and alerting rules

### **When Adding New Features**
- [ ] Implement comprehensive input validation
- [ ] Add timeout handling for external calls
- [ ] Include graceful degradation paths
- [ ] Add comprehensive error logging
- [ ] Test failure scenarios thoroughly

---

## 🎯 **Success Metrics**

**Defensive Programming Effectiveness**:
- **Uptime**: >99.9% availability
- **Error Recovery**: <1% unhandled errors  
- **Response Times**: 95% of requests <1s
- **Graceful Degradation**: No cascading failures
- **User Experience**: Clear error messages, no UI breakage

**Monthly Review Questions**:
1. Are we catching and handling all error conditions?
2. Do timeout values match actual usage patterns?
3. Are fallback mechanisms preventing user frustration?
4. Is the system self-healing where possible?
5. Are we providing clear, actionable error messages?

---

## 📞 **Support & Troubleshooting**

### **When Issues Arise**

**Immediate Response** (First 15 minutes):
1. Check health endpoints: `/health`, `/api/agents/list`
2. Review recent error logs for patterns
3. Verify all services are running (Docker containers)
4. Test agent availability and response times

**Short-term Fix** (Within 1 hour):
1. Restart affected services if needed
2. Implement temporary workarounds
3. Increase timeouts if performance is degraded
4. Switch to fallback modes if available

**Long-term Resolution** (Within 24 hours):
1. Root cause analysis of defensive mechanisms that failed
2. Implement additional safeguards
3. Update monitoring to prevent recurrence
4. Document lessons learned and update this guide

### **Key Files for Troubleshooting**

**Backend**:
- `apps/api/app/api/endpoints/tasks.py` - Task API with timeout handling
- `apps/api/app/api/endpoints/agent_management.py` - Agent endpoints
- `apps/api/app/database.py` - Connection pooling
- `apps/api/app/main.py` - Application startup and configuration

**Frontend**:
- `apps/web/lib/api.ts` - API client with timeout handling
- `apps/web/lib/store.ts` - State management with error handling
- `apps/web/components/pipeline/steps/` - UI components with validation

**Configuration**:
- `docker-compose.yml` - Service configuration
- `apps/api/.env` - Environment variables
- `apps/api/app/config.py` - Application settings

---

This maintenance guide ensures the Threat Modeling Pipeline remains robust, performant, and user-friendly through proactive defensive programming practices. Regular adherence to these guidelines will maintain the high-quality, enterprise-grade architecture that prevents issues before they impact users.