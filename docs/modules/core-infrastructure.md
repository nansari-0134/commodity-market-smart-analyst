# Core Infrastructure & Base Architecture

The `apps/core` module delivers the fundamental architectural substrate for the entire commodity intelligence platform.

---

## 1. Module Overview & Purpose

Institutional commodity data pipelines process millions of tick-level and daily observations across distributed microservices. This module guarantees:

- **Universal Entity Tracking**: All business entities use universally unique identifiers (UUIDv4) to prevent integer enumeration attacks and enable seamless cross-database replication.
- **Audit Trails**: Every database table automatically tracks its creation and last-modified UTC timestamps.
- **System Health Probes**: High-speed, lightweight endpoints for Kubernetes, Docker health checks, and load balancers to monitor database and cache connectivity.

---

## 2. Architecture & Data Flow

```mermaid
graph LR
    Subclass[Domain Model<br/>e.g. ExchangeMaster] -->|inherits| UUIDModel[UUIDModel<br/>UUIDv4 Primary Key]
    Subclass -->|inherits| TimeStamped[TimeStampedModel<br/>created_at & updated_at UTC]
    Probe[Monitoring Agent / Orchestrator] -->|GET /health/| HealthView[health_check view]
    HealthView -->|Ping| DB[(PostgreSQL / SQLite)]
```

---

## 3. Core Models & Abstractions

### `UUIDModel`
Located in `apps/core/models.py`. An abstract Django model providing a cryptographically random UUID primary key:

```python
class UUIDModel(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Universally unique record identifier (UUIDv4)",
    )
```

### `TimeStampedModel`
Located in `apps/core/models.py`. An abstract Django model maintaining timezone-aware UTC audit fields:

```python
class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### `AbstractObservation`
Abstract base model establishing the platform's high-performance standard for time series metrics:
* **Storage Standard**: Missing/unobserved numeric values are strictly stored as SQL native `NULL` (`null=True, blank=True`). This avoids 20-40% database bloat caused by redundant status strings and leverages native 1-bit null bitmaps.
* **Vectorized Math**: Maps directly to IEEE 754 `np.nan` in Pandas/NumPy, enabling C-speed SIMD operations (`df.interpolate()`, `df.ffill()`, `df.dropna()`).
* **Boundary Integrity**: Distinguishes between legitimate `0.0` observations (e.g., zero rainfall, zero pipeline throughput) and unobserved `NULL` points.
* **Presentation Layer**: Exposes `is_available` boolean and `display_value` rendering `"NOT_AVAILABLE"` dynamically for REST APIs and LLM context prompts.

### `DataQualityStatus`
Standardized enumeration for data curation and provenance:
- `VALID`: Verified observation conforming to constraints.
- `WARNING`: Observation flagged with mild statistical outlier or boundary condition.
- `INVALID`: Failed validation check.
- `MISSING`: Unobserved / unavailable point-in-time slot.
- `STALE`: Value carried forward or delayed beyond SLA.
- `DUPLICATE`: Repeated record flagged for deduplication.
- `SUSPECT`: Questionable variance flagged for human audit.

---

## 4. How to Extend / Change Infrastructure Components

### Adding a Custom Health Diagnostic Probe
If you want to add a health check for an external message queue (e.g. Celery / Redis) or database cluster:

- **Target File**: `apps/core/views.py`
- **Target Function**: `SystemStatusAPIView.get(self, request)`

#### Implementation Contract:
```python
# In apps/core/views.py:

class SystemStatusAPIView(APIView):
    def get(self, request):
        # 1. Probe database
        db_healthy = self._check_db()
        
        # 2. Probe Redis / Celery (Example extension)
        redis_healthy = self._check_redis()
        
        overall_healthy = db_healthy and redis_healthy
        
        return Response({
            "status": "online" if overall_healthy else "degraded",
            "services": {
                "database": db_healthy,
                "cache_redis": redis_healthy,
            }
        }, status=200 if overall_healthy else 503)
```
