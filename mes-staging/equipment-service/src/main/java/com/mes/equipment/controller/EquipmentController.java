package com.mes.equipment.controller;
import com.mes.equipment.dto.TelemetryRequest;
import com.mes.equipment.entity.Equipment;
import com.mes.equipment.service.EquipmentService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/equipment")
public class EquipmentController {
    private final EquipmentService service;
    public EquipmentController(EquipmentService service) { this.service = service; }

    @PostMapping
    public ResponseEntity<Equipment> register(@RequestBody Equipment e) {
        return ResponseEntity.status(HttpStatus.CREATED).body(service.register(e));
    }
    @GetMapping("/{id}")
    public Equipment get(@PathVariable String id) { return service.get(id); }
    @GetMapping
    public List<Equipment> list(@RequestParam(required=false) String status) {
        return status == null ? service.listAll() : service.listByStatus(status);
    }
    @PutMapping("/{id}/status")
    public Equipment updateStatus(@PathVariable String id, @RequestParam String status) {
        return service.updateStatus(id, status);
    }
    @PostMapping("/{id}/telemetry")
    public Equipment telemetry(@PathVariable String id, @RequestBody TelemetryRequest t) {
        return service.ingestTelemetry(id, t);
    }
    @GetMapping("/metrics/oee")
    public Map<String,Object> oee() { return Map.of("oee", service.overallEquipmentEffectiveness(), "unit","percent"); }
    @GetMapping("/metrics/cache")
    public Map<String,Object> cacheStats() { return service.cacheStats(); }
}
