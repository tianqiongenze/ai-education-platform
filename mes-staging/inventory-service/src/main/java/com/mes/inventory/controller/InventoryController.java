package com.mes.inventory.controller;
import com.mes.inventory.dto.StockMovementRequest;
import com.mes.inventory.entity.Material;
import com.mes.inventory.service.InventoryService;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/inventory")
public class InventoryController {
    private final InventoryService service;
    public InventoryController(InventoryService service) { this.service = service; }

    @PostMapping("/materials")
    public ResponseEntity<Material> create(@RequestBody Material m) {
        return ResponseEntity.status(HttpStatus.CREATED).body(service.createMaterial(m));
    }
    @GetMapping("/materials")
    public List<Material> list() { return service.listAll(); }
    @GetMapping("/materials/{sku}")
    public Material bySku(@PathVariable String sku) { return service.getBySku(sku); }
    @GetMapping("/materials/low-stock")
    public List<Material> lowStock() { return service.listLowStock(); }
    @GetMapping("/materials/critical")
    public List<Material> critical() { return service.listCritical(); }
    @PostMapping("/movements")
    public Material move(@Valid @RequestBody StockMovementRequest req) { return service.moveStock(req); }
    @GetMapping("/metrics/value")
    public Map<String,Object> value() { return Map.of("inventoryValue", service.inventoryValue(), "currency","CNY"); }
    @GetMapping("/metrics/cache")
    public Map<String,Object> cacheStats() { return service.cacheStats(); }
}
