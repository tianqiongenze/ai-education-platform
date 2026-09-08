package com.mes.quality.service;
import com.mes.cache.CacheMetrics;
import com.mes.quality.dto.InspectionRequest;
import com.mes.quality.entity.InspectionRecord;
import com.mes.quality.repository.InspectionRepository;
import org.springframework.cache.annotation.CacheEvict;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.cache.annotation.Caching;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import java.util.List;

@Service
public class QualityService {
    private static final List<String> VALID_RESULTS = List.of("PASS","FAIL","PENDING");
    private final InspectionRepository repo;
    private final CacheMetrics cacheMetrics;
    public QualityService(InspectionRepository repo, CacheMetrics cacheMetrics) {
        this.repo = repo; this.cacheMetrics = cacheMetrics;
    }

    @Transactional
    @Caching(evict = {
        @CacheEvict(value = "qualityInspections", allEntries = true),
        @CacheEvict(value = "qualityMetrics", allEntries = true)
    })
    public InspectionRecord recordInspection(InspectionRequest req) {
        if (req.getSampleSize() <= 0) throw new IllegalArgumentException("sampleSize must be positive");
        if (req.getPassed() < 0 || req.getFailed() < 0) throw new IllegalArgumentException("counts cannot be negative");
        if (req.getPassed() + req.getFailed() != req.getSampleSize())
            throw new IllegalArgumentException("passed + failed must equal sampleSize");
        String result = req.getFailed() == 0 ? "PASS" : "FAIL";
        InspectionRecord rec = new InspectionRecord(req.getProductionOrderId(), req.getProductCode(),
                req.getSampleSize(), req.getPassed(), req.getFailed());
        rec.setInspector(req.getInspector());
        rec.setDefectType(req.getDefectType());
        rec.setResult(result);
        return repo.save(rec);
    }

    @Transactional(readOnly = true)
    @Cacheable(value = "qualityInspections", key = "#id")
    public InspectionRecord getInspection(String id) {
        return repo.findById(id).orElseThrow(() -> new IllegalArgumentException("inspection not found: " + id));
    }

    @Transactional(readOnly = true)
    @Cacheable(value = "qualityInspections", key = "'order:' + #orderId")
    public List<InspectionRecord> listByOrder(String orderId) { return repo.findByProductionOrderId(orderId); }

    @Transactional(readOnly = true)
    @Cacheable(value = "qualityMetrics", key = "'fpy'")
    public double firstPassYield() {
        int passed = repo.totalPassed();
        int failed = repo.totalFailed();
        int total = passed + failed;
        if (total == 0) return 0.0;
        return (double) passed / total * 100.0;
    }

    @Transactional(readOnly = true)
    @Cacheable(value = "qualityMetrics", key = "'defectRate'")
    public double defectRate() {
        int passed = repo.totalPassed();
        int failed = repo.totalFailed();
        int total = passed + failed;
        if (total == 0) return 0.0;
        return (double) failed / total * 100.0;
    }

    public java.util.Map<String, Object> cacheStats() { return cacheMetrics.snapshot(); }
}
