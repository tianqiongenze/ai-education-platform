package com.mes.equipment.service;
import com.mes.cache.CacheMetrics;
import com.mes.equipment.dto.TelemetryRequest;
import com.mes.equipment.entity.Equipment;
import com.mes.equipment.repository.EquipmentRepository;
import org.springframework.cache.annotation.CacheEvict;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.cache.annotation.Caching;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import java.util.List;

@Service
public class EquipmentService {
    private static final List<String> VALID_STATUSES = List.of("IDLE","RUNNING","FAULT","MAINTENANCE","OFFLINE");
    private static final double TEMP_WARN = 85.0;
    private static final double TEMP_CRIT = 95.0;
    private static final double VIB_WARN = 5.0;
    private static final double VIB_CRIT = 8.0;
    private final EquipmentRepository repo;
    private final CacheMetrics cacheMetrics;
    public EquipmentService(EquipmentRepository repo, CacheMetrics cacheMetrics) {
        this.repo = repo; this.cacheMetrics = cacheMetrics;
    }

    @Transactional
    @CacheEvict(value = "equipment", allEntries = true)
    public Equipment register(Equipment e) {
        if (repo.findByCode(e.getCode()).isPresent())
            throw new IllegalArgumentException("equipment code already exists: " + e.getCode());
        if (e.getStatus() == null) e.setStatus("IDLE");
        return repo.save(e);
    }

    @Transactional(readOnly = true)
    @Cacheable(value = "equipment", key = "#id")
    public Equipment get(String id) {
        return repo.findById(id).orElseThrow(() -> new IllegalArgumentException("equipment not found: " + id));
    }

    @Transactional(readOnly = true)
    @Cacheable(value = "equipment", key = "'status:' + #status")
    public List<Equipment> listByStatus(String status) {
        validateStatus(status);
        return repo.findByStatus(status);
    }

    @Transactional(readOnly = true)
    @Cacheable(value = "equipment", key = "'all'")
    public List<Equipment> listAll() { return repo.findAll(); }

    @Transactional
    @Caching(evict = {
        @CacheEvict(value = "equipment", allEntries = true),
        @CacheEvict(value = "equipmentMetrics", allEntries = true)
    })
    public Equipment updateStatus(String id, String status) {
        validateStatus(status);
        Equipment e = get(id);
        e.setStatus(status);
        return repo.save(e);
    }

    /** Apply telemetry and run predictive maintenance checks. Returns the updated equipment. */
    @Transactional
    @Caching(evict = {
        @CacheEvict(value = "equipment", allEntries = true),
        @CacheEvict(value = "equipmentMetrics", allEntries = true)
    })
    public Equipment ingestTelemetry(String id, TelemetryRequest t) {
        Equipment e = get(id);
        e.setTemperature(t.getTemperature());
        e.setVibration(t.getVibration());
        e.setRpm(t.getRpm());
        // predictive rule: auto-flag FAULT when critical thresholds exceeded
        String predicted = predictStatus(t);
        if ("FAULT".equals(predicted) && !"MAINTENANCE".equals(e.getStatus())) {
            e.setStatus("FAULT");
        } else if (e.getStatus().equals("IDLE") && t.getRpm() > 0) {
            e.setStatus("RUNNING");
        } else if (e.getStatus().equals("RUNNING") && t.getRpm() == 0) {
            e.setStatus("IDLE");
        }
        // utilization tracking: running equipment accrues utilization up to 100%
        if ("RUNNING".equals(e.getStatus())) {
            e.setUtilizationRate(Math.min(100.0, e.getUtilizationRate() + 0.1));
        }
        return repo.save(e);
    }

    String predictStatus(TelemetryRequest t) {
        if (t.getTemperature() >= TEMP_CRIT || t.getVibration() >= VIB_CRIT) return "FAULT";
        if (t.getTemperature() >= TEMP_WARN || t.getVibration() >= VIB_WARN) return "MAINTENANCE";
        return "RUNNING";
    }

    @Transactional(readOnly = true)
    @Cacheable(value = "equipmentMetrics", key = "'oee'")
    public double overallEquipmentEffectiveness() {
        double util = repo.averageUtilization();
        long running = repo.countByStatus("RUNNING");
        long total = repo.count();
        long faulted = repo.countByStatus("FAULT");
        double availability = total == 0 ? 0.0 : (double)(total - faulted) / total * 100.0;
        double performance = running == 0 ? 0.0 : 100.0;
        return availability * (util/100.0) * performance / 100.0;
    }

    public java.util.Map<String, Object> cacheStats() { return cacheMetrics.snapshot(); }

    private void validateStatus(String s) { if (!VALID_STATUSES.contains(s)) throw new IllegalArgumentException("invalid status: " + s); }
}
