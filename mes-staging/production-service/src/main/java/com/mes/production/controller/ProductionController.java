package com.mes.production.controller;
import com.mes.production.dto.ProductionOrderRequest;
import com.mes.production.dto.ProductionOrderResponse;
import com.mes.production.service.ProductionService;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/production/orders")
public class ProductionController {
    private final ProductionService service;
    public ProductionController(ProductionService service) { this.service = service; }

    @PostMapping
    public ResponseEntity<ProductionOrderResponse> create(@Valid @RequestBody ProductionOrderRequest req) {
        return ResponseEntity.status(HttpStatus.CREATED).body(service.createOrder(req));
    }

    @GetMapping("/{id}")
    public ProductionOrderResponse get(@PathVariable String id) { return service.getOrder(id); }

    @GetMapping
    public List<ProductionOrderResponse> list(@RequestParam(required=false) String status) {
        return status == null ? service.listAll() : service.listByStatus(status);
    }

    @PostMapping("/{id}/start")
    public ProductionOrderResponse start(@PathVariable String id) { return service.startProduction(id); }

    @PostMapping("/{id}/progress")
    public ProductionOrderResponse progress(@PathVariable String id, @RequestParam int completed,
                                           @RequestParam int defects) {
        return service.reportProgress(id, completed, defects);
    }

    @PostMapping("/{id}/cancel")
    public ProductionOrderResponse cancel(@PathVariable String id) { return service.cancelOrder(id); }

    @GetMapping("/metrics/yield-rate")
    public Map<String, Object> yieldRate() {
        return Map.of("yieldRate", service.calculateYieldRate(), "unit", "percent");
    }

    @GetMapping("/metrics/cache")
    public Map<String, Object> cacheStats() {
        return service.cacheStats();
    }
}
