package com.mes.inventory.service;
import com.mes.cache.CacheMetrics;
import com.mes.inventory.dto.StockMovementRequest;
import com.mes.inventory.entity.Material;
import com.mes.inventory.repository.MaterialRepository;
import org.springframework.cache.annotation.CacheEvict;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.cache.annotation.Caching;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import java.time.LocalDateTime;
import java.util.List;

@Service
public class InventoryService {
    private static final List<String> VALID_TYPES = List.of("IN","OUT","ADJUST");
    private final MaterialRepository repo;
    private final CacheMetrics cacheMetrics;
    public InventoryService(MaterialRepository repo, CacheMetrics cacheMetrics) {
        this.repo = repo; this.cacheMetrics = cacheMetrics;
    }

    @Transactional
    @CacheEvict(value = "materials", allEntries = true)
    public Material createMaterial(Material m) {
        if (repo.findBySku(m.getSku()).isPresent())
            throw new IllegalArgumentException("sku already exists: " + m.getSku());
        return repo.save(m);
    }

    @Transactional(readOnly = true)
    @Cacheable(value = "materials", key = "#id")
    public Material get(String id) {
        return repo.findById(id).orElseThrow(() -> new IllegalArgumentException("material not found: " + id));
    }

    @Transactional(readOnly = true)
    @Cacheable(value = "materials", key = "'sku:' + #sku")
    public Material getBySku(String sku) {
        return repo.findBySku(sku).orElseThrow(() -> new IllegalArgumentException("material not found: " + sku));
    }

    @Transactional(readOnly = true)
    @Cacheable(value = "materials", key = "'all'")
    public List<Material> listAll() { return repo.findAll(); }

    @Transactional(readOnly = true)
    @Cacheable(value = "materials", key = "'low-stock'")
    public List<Material> listLowStock() { return repo.findBelowReorderPoint(); }

    @Transactional(readOnly = true)
    @Cacheable(value = "materials", key = "'critical'")
    public List<Material> listCritical() { return repo.findBelowSafetyStock(); }

    @Transactional
    @Caching(evict = {
        @CacheEvict(value = "materials", allEntries = true),
        @CacheEvict(value = "inventoryMetrics", allEntries = true)
    })
    public Material moveStock(StockMovementRequest req) {
        validateType(req.getType());
        Material m = getBySku(req.getSku());
        int delta = switch (req.getType()) {
            case "IN" -> req.getQuantity();
            case "OUT" -> -req.getQuantity();
            case "ADJUST" -> req.getQuantity(); // signed adjustment
            default -> throw new IllegalArgumentException("invalid type");
        };
        int newQty = m.getQuantity() + delta;
        if (newQty < 0) throw new IllegalStateException("insufficient stock: have " + m.getQuantity() + ", want to remove " + req.getQuantity());
        m.setQuantity(newQty);
        m.setUpdatedAt(LocalDateTime.now());
        return repo.save(m);
    }

    @Transactional(readOnly = true)
    @Cacheable(value = "inventoryMetrics", key = "'value'")
    public double inventoryValue() { return repo.totalInventoryValue(); }

    public java.util.Map<String, Object> cacheStats() { return cacheMetrics.snapshot(); }

    private void validateType(String t) { if (!VALID_TYPES.contains(t)) throw new IllegalArgumentException("invalid type: " + t); }
}
