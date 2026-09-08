package com.mes.quality.controller;
import com.mes.quality.dto.InspectionRequest;
import com.mes.quality.entity.InspectionRecord;
import com.mes.quality.service.QualityService;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/quality/inspections")
public class QualityController {
    private final QualityService service;
    public QualityController(QualityService service) { this.service = service; }

    @PostMapping
    public ResponseEntity<InspectionRecord> create(@Valid @RequestBody InspectionRequest req) {
        return ResponseEntity.status(HttpStatus.CREATED).body(service.recordInspection(req));
    }
    @GetMapping("/{id}")
    public InspectionRecord get(@PathVariable String id) { return service.getInspection(id); }
    @GetMapping
    public List<InspectionRecord> byOrder(@RequestParam String orderId) { return service.listByOrder(orderId); }

    @GetMapping("/metrics/fpy")
    public Map<String,Object> firstPassYield() { return Map.of("firstPassYield", service.firstPassYield(), "unit","percent"); }
    @GetMapping("/metrics/defect-rate")
    public Map<String,Object> defectRate() { return Map.of("defectRate", service.defectRate(), "unit","percent"); }
    @GetMapping("/metrics/cache")
    public Map<String,Object> cacheStats() { return service.cacheStats(); }
}
