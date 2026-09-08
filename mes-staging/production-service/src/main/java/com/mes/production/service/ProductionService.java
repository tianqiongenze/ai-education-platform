package com.mes.production.service;
import com.mes.cache.CacheMetrics;
import com.mes.production.dto.ProductionOrderRequest;
import com.mes.production.dto.ProductionOrderResponse;
import com.mes.production.entity.ProductionOrder;
import com.mes.production.repository.ProductionOrderRepository;
import org.springframework.cache.annotation.CacheEvict;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.cache.annotation.Caching;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import java.time.LocalDateTime;
import java.util.List;
import java.util.stream.Collectors;

@Service
public class ProductionService {
    private static final List<String> VALID_STATUSES = List.of("CREATED","IN_PROGRESS","COMPLETED","CANCELLED");
    private static final List<String> VALID_PRIORITIES = List.of("LOW","NORMAL","HIGH","URGENT");
    private final ProductionOrderRepository repo;
    private final CacheMetrics cacheMetrics;
    public ProductionService(ProductionOrderRepository repo, CacheMetrics cacheMetrics) {
        this.repo = repo; this.cacheMetrics = cacheMetrics;
    }

    @Transactional
    @Caching(evict = {
        @CacheEvict(value = "productionOrders", allEntries = true),
        @CacheEvict(value = "orderMetrics", allEntries = true)
    })
    public ProductionOrderResponse createOrder(ProductionOrderRequest req) {
        validatePriority(req.getPriority());
        if (req.getQuantity() <= 0) throw new IllegalArgumentException("quantity must be positive");
        ProductionOrder o = new ProductionOrder(req.getProductCode(), req.getQuantity(), req.getPriority());
        o.setWorkCenter(req.getWorkCenter());
        o.setAssignedOperator(req.getAssignedOperator());
        return toResp(repo.save(o));
    }

    @Transactional(readOnly = true)
    @Cacheable(value = "productionOrders", key = "#id", unless = "#result == null")
    public ProductionOrderResponse getOrder(String id) {
        return repo.findById(id).map(this::toResp)
                .orElseThrow(() -> new IllegalArgumentException("order not found: " + id));
    }

    @Transactional(readOnly = true)
    @Cacheable(value = "productionOrders", key = "'status:' + #status")
    public List<ProductionOrderResponse> listByStatus(String status) {
        validateStatus(status);
        return repo.findByStatus(status).stream().map(this::toResp).collect(Collectors.toList());
    }

    @Transactional(readOnly = true)
    @Cacheable(value = "productionOrders", key = "'all'")
    public List<ProductionOrderResponse> listAll() {
        return repo.findAll().stream().map(this::toResp).collect(Collectors.toList());
    }

    @Transactional
    @Caching(evict = {
        @CacheEvict(value = "productionOrders", allEntries = true),
        @CacheEvict(value = "orderMetrics", allEntries = true)
    })
    public ProductionOrderResponse startProduction(String id) {
        ProductionOrder o = findById(id);
        if (!"CREATED".equals(o.getStatus())) {
            throw new IllegalStateException("only CREATED orders can start, current=" + o.getStatus());
        }
        o.setStatus("IN_PROGRESS");
        o.setActualStart(LocalDateTime.now());
        o.setUpdatedAt(LocalDateTime.now());
        return toResp(repo.save(o));
    }

    @Transactional
    @Caching(evict = {
        @CacheEvict(value = "productionOrders", allEntries = true),
        @CacheEvict(value = "orderMetrics", allEntries = true)
    })
    public ProductionOrderResponse reportProgress(String id, int completed, int defects) {
        ProductionOrder o = findById(id);
        if (!"IN_PROGRESS".equals(o.getStatus())) {
            throw new IllegalStateException("can only report progress on IN_PROGRESS orders");
        }
        if (completed < 0 || defects < 0) throw new IllegalArgumentException("quantities cannot be negative");
        o.setCompletedQuantity(o.getCompletedQuantity() + completed);
        o.setDefectCount(o.getDefectCount() + defects);
        o.setUpdatedAt(LocalDateTime.now());
        if (o.getCompletedQuantity() >= o.getQuantity()) {
            o.setStatus("COMPLETED");
            o.setActualEnd(LocalDateTime.now());
        }
        return toResp(repo.save(o));
    }

    @Transactional
    @Caching(evict = {
        @CacheEvict(value = "productionOrders", allEntries = true),
        @CacheEvict(value = "orderMetrics", allEntries = true)
    })
    public ProductionOrderResponse cancelOrder(String id) {
        ProductionOrder o = findById(id);
        if ("COMPLETED".equals(o.getStatus())) {
            throw new IllegalStateException("cannot cancel a COMPLETED order");
        }
        o.setStatus("CANCELLED");
        o.setUpdatedAt(LocalDateTime.now());
        return toResp(repo.save(o));
    }

    @Transactional(readOnly = true)
    @Cacheable(value = "orderMetrics", key = "'yieldRate'")
    public double calculateYieldRate() {
        int completed = repo.totalQuantityByStatus("COMPLETED");
        int defects = repo.totalDefects();
        if (completed == 0) return 0.0;
        return Math.max(0.0, (double)(completed - defects) / completed * 100.0);
    }

    /** Expose cache hit/miss stats for analysis. */
    public java.util.Map<String, Object> cacheStats() { return cacheMetrics.snapshot(); }

    private ProductionOrder findById(String id) {
        return repo.findById(id).orElseThrow(() -> new IllegalArgumentException("order not found: " + id));
    }
    private void validateStatus(String s) { if (!VALID_STATUSES.contains(s)) throw new IllegalArgumentException("invalid status: " + s); }
    private void validatePriority(String p) { if (!VALID_PRIORITIES.contains(p)) throw new IllegalArgumentException("invalid priority: " + p); }

    private ProductionOrderResponse toResp(ProductionOrder o) {
        return new ProductionOrderResponse(o.getId(), o.getProductCode(), o.getQuantity(),
            o.getCompletedQuantity(), o.getDefectCount(), o.getStatus(), o.getPriority(),
            o.getWorkCenter(), o.getAssignedOperator(), o.getPlannedStart(), o.getPlannedEnd(),
            o.getActualStart(), o.getActualEnd(), o.getCreatedAt());
    }
}
