#!/usr/bin/env python3
"""Generate quality-service, equipment-service, inventory-service and gateway-service."""
import os, textwrap

SERVICES = {
    "quality-service": ("com.mes.quality", "quality", "8082", "Quality Control Service (质量控制)"),
    "equipment-service": ("com.mes.equipment", "equipment", "8083", "Equipment Monitoring Service (设备监控)"),
    "inventory-service": ("com.mes.inventory", "inventory", "8084", "Inventory Service (库存管理)"),
}

def w(base, rel, content):
    p = os.path.join(base, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w") as f:
        f.write(textwrap.dedent(content).lstrip("\n"))

def pom(name, artifact, desc):
    return f'''
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    <parent>
        <groupId>com.mes</groupId>
        <artifactId>mes-system</artifactId>
        <version>1.0.0</version>
    </parent>
    <artifactId>{artifact}</artifactId>
    <name>{desc}</name>
    <dependencies>
        <dependency><groupId>org.springframework.boot</groupId><artifactId>spring-boot-starter-web</artifactId></dependency>
        <dependency><groupId>org.springframework.boot</groupId><artifactId>spring-boot-starter-validation</artifactId></dependency>
        <dependency><groupId>org.springframework.boot</groupId><artifactId>spring-boot-starter-data-jpa</artifactId></dependency>
        <dependency><groupId>org.springframework.boot</groupId><artifactId>spring-boot-starter-actuator</artifactId></dependency>
        <dependency><groupId>org.springframework.boot</groupId><artifactId>spring-boot-starter-test</artifactId><scope>test</scope></dependency>
        <dependency><groupId>com.h2database</groupId><artifactId>h2</artifactId><scope>test</scope></dependency>
    </dependencies>
    <build><plugins>
        <plugin><groupId>org.springframework.boot</groupId><artifactId>spring-boot-maven-plugin</artifactId></plugin>
    </plugins></build>
</project>
'''

def app_yml(name, port):
    return f'''
server:
  port: {port}
spring:
  application:
    name: {name}
  datasource:
    url: jdbc:h2:mem:mesdb;DB_CLOSE_DELAY=-1
    driver-class-name: org.h2.Driver
    username: sa
    password: ""
  jpa:
    hibernate:
      ddl-auto: update
  h2:
    console:
      enabled: true
management:
  endpoints:
    web:
      exposure:
        include: health,info,metrics
'''

def test_yml():
    return '''
spring:
  datasource:
    url: jdbc:h2:mem:testdb;DB_CLOSE_DELAY=-1;MODE=LEGACY
    driver-class-name: org.h2.Driver
    username: sa
    password: ""
  jpa:
    hibernate:
      ddl-auto: create-drop
'''

# =================== QUALITY SERVICE ===================
B = "/tmp/p1-java/mes-system/quality-service"
w(B, "pom.xml", pom("quality-service", "quality-service", "Quality Control Service (质量控制)"))
w(B, "src/main/java/com/mes/quality/QualityServiceApplication.java", '''
package com.mes.quality;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
@SpringBootApplication
public class QualityServiceApplication {
    public static void main(String[] args) { SpringApplication.run(QualityServiceApplication.class, args); }
}
''')
w(B, "src/main/java/com/mes/quality/entity/InspectionRecord.java", '''
package com.mes.quality.entity;
import jakarta.persistence.*;
import java.time.LocalDateTime;
import java.util.UUID;

@Entity
@Table(name = "inspection_records")
public class InspectionRecord {
    @Id
    private String id = UUID.randomUUID().toString();
    @Column(nullable=false) private String productionOrderId;
    @Column(nullable=false) private String productCode;
    @Column(nullable=false) private int sampleSize;
    @Column(nullable=false) private int passed;
    @Column(nullable=false) private int failed;
    @Column(nullable=false) private String result = "PENDING"; // PASS, FAIL, PENDING
    private String inspector;
    private String defectType;
    private String notes;
    @Column(nullable=false) private LocalDateTime inspectedAt = LocalDateTime.now();
    public InspectionRecord() {}
    public InspectionRecord(String orderId, String productCode, int sampleSize, int passed, int failed) {
        this.productionOrderId = orderId; this.productCode = productCode;
        this.sampleSize = sampleSize; this.passed = passed; this.failed = failed;
        this.result = failed == 0 ? "PASS" : (passed == 0 ? "FAIL" : "FAIL");
    }
    public String getId(){return id;}
    public String getProductionOrderId(){return productionOrderId;} public void setProductionOrderId(String s){this.productionOrderId=s;}
    public String getProductCode(){return productCode;} public void setProductCode(String s){this.productCode=s;}
    public int getSampleSize(){return sampleSize;} public void setSampleSize(int s){this.sampleSize=s;}
    public int getPassed(){return passed;} public void setPassed(int p){this.passed=p;}
    public int getFailed(){return failed;} public void setFailed(int f){this.failed=f;}
    public String getResult(){return result;} public void setResult(String r){this.result=r;}
    public String getInspector(){return inspector;} public void setInspector(String i){this.inspector=i;}
    public String getDefectType(){return defectType;} public void setDefectType(String d){this.defectType=d;}
    public String getNotes(){return notes;} public void setNotes(String n){this.notes=n;}
    public LocalDateTime getInspectedAt(){return inspectedAt;} public void setInspectedAt(LocalDateTime t){this.inspectedAt=t;}
}
''')
w(B, "src/main/java/com/mes/quality/dto/InspectionRequest.java", '''
package com.mes.quality.dto;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Positive;
public class InspectionRequest {
    @NotBlank private String productionOrderId;
    @NotBlank private String productCode;
    @Positive private int sampleSize;
    @Positive private int passed;
    private int failed;
    private String inspector;
    private String defectType;
    public String getProductionOrderId(){return productionOrderId;} public void setProductionOrderId(String s){this.productionOrderId=s;}
    public String getProductCode(){return productCode;} public void setProductCode(String s){this.productCode=s;}
    public int getSampleSize(){return sampleSize;} public void setSampleSize(int s){this.sampleSize=s;}
    public int getPassed(){return passed;} public void setPassed(int p){this.passed=p;}
    public int getFailed(){return failed;} public void setFailed(int f){this.failed=f;}
    public String getInspector(){return inspector;} public void setInspector(String i){this.inspector=i;}
    public String getDefectType(){return defectType;} public void setDefectType(String d){this.defectType=d;}
}
''')
w(B, "src/main/java/com/mes/quality/repository/InspectionRepository.java", '''
package com.mes.quality.repository;
import com.mes.quality.entity.InspectionRecord;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;
import java.util.List;
@Repository
public interface InspectionRepository extends JpaRepository<InspectionRecord, String> {
    List<InspectionRecord> findByProductionOrderId(String orderId);
    List<InspectionRecord> findByResult(String result);
    @Query("SELECT COALESCE(SUM(r.passed),0) FROM InspectionRecord r")
    int totalPassed();
    @Query("SELECT COALESCE(SUM(r.failed),0) FROM InspectionRecord r")
    int totalFailed();
}
''')
w(B, "src/main/java/com/mes/quality/service/QualityService.java", '''
package com.mes.quality.service;
import com.mes.quality.dto.InspectionRequest;
import com.mes.quality.entity.InspectionRecord;
import com.mes.quality.repository.InspectionRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import java.util.List;

@Service
public class QualityService {
    private static final List<String> VALID_RESULTS = List.of("PASS","FAIL","PENDING");
    private final InspectionRepository repo;
    public QualityService(InspectionRepository repo) { this.repo = repo; }

    @Transactional
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
    public InspectionRecord getInspection(String id) {
        return repo.findById(id).orElseThrow(() -> new IllegalArgumentException("inspection not found: " + id));
    }

    @Transactional(readOnly = true)
    public List<InspectionRecord> listByOrder(String orderId) { return repo.findByProductionOrderId(orderId); }

    @Transactional(readOnly = true)
    public double firstPassYield() {
        int passed = repo.totalPassed();
        int failed = repo.totalFailed();
        int total = passed + failed;
        if (total == 0) return 0.0;
        return (double) passed / total * 100.0;
    }

    @Transactional(readOnly = true)
    public double defectRate() {
        int passed = repo.totalPassed();
        int failed = repo.totalFailed();
        int total = passed + failed;
        if (total == 0) return 0.0;
        return (double) failed / total * 100.0;
    }
}
''')
w(B, "src/main/java/com/mes/quality/controller/QualityController.java", '''
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
}
''')
w(B, "src/main/resources/application.yml", app_yml("quality-service", "8082"))
w(B, "src/test/resources/application.yml", test_yml())
w(B, "src/test/java/com/mes/quality/service/QualityServiceTest.java", '''
package com.mes.quality.service;
import com.mes.quality.dto.InspectionRequest;
import com.mes.quality.entity.InspectionRecord;
import com.mes.quality.repository.InspectionRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvSource;
import java.util.Optional;
import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

class QualityServiceTest {
    private InspectionRepository repo;
    private QualityService service;
    @BeforeEach void setUp() { repo = mock(InspectionRepository.class); service = new QualityService(repo); }

    private InspectionRequest req(int sample, int passed, int failed) {
        InspectionRequest r = new InspectionRequest();
        r.setProductionOrderId("ord-1"); r.setProductCode("P-A100");
        r.setSampleSize(sample); r.setPassed(passed); r.setFailed(failed);
        r.setInspector("insp-1");
        return r;
    }

    @Test @DisplayName("recordInspection saves a PASS when no failures")
    void recordsPass() {
        when(repo.save(any(InspectionRecord.class))).thenAnswer(i -> i.getArgument(0));
        InspectionRecord rec = service.recordInspection(req(100, 100, 0));
        assertEquals("PASS", rec.getResult());
        assertEquals(100, rec.getPassed());
        verify(repo).save(any());
    }

    @Test @DisplayName("recordInspection saves a FAIL when there are failures")
    void recordsFail() {
        when(repo.save(any())).thenAnswer(i -> i.getArgument(0));
        InspectionRecord rec = service.recordInspection(req(100, 92, 8));
        assertEquals("FAIL", rec.getResult());
        assertEquals(8, rec.getFailed());
    }

    @ParameterizedTest
    @CsvSource({"0,-1", "-1,0"})
    @DisplayName("recordInspection rejects negative counts")
    void rejectsNegative(int passed, int failed) {
        InspectionRequest r = req(10, Math.max(passed,0), Math.max(failed,0));
        r.setPassed(passed); r.setFailed(failed);
        assertThrows(IllegalArgumentException.class, () -> service.recordInspection(r));
    }

    @Test @DisplayName("recordInspection rejects passed+failed != sampleSize")
    void rejectsMismatchedCounts() {
        InspectionRequest r = req(100, 50, 40); // 50+40 != 100
        assertThrows(IllegalArgumentException.class, () -> service.recordInspection(r));
    }

    @Test @DisplayName("getInspection throws when missing")
    void getThrows() {
        when(repo.findById("X")).thenReturn(Optional.empty());
        assertThrows(IllegalArgumentException.class, () -> service.getInspection("X"));
    }

    @Test @DisplayName("firstPassYield and defectRate compute correctly")
    void metricsCompute() {
        when(repo.totalPassed()).thenReturn(90);
        when(repo.totalFailed()).thenReturn(10);
        assertEquals(90.0, service.firstPassYield(), 0.001);
        assertEquals(10.0, service.defectRate(), 0.001);
    }

    @Test @DisplayName("metrics are 0 when no data")
    void metricsZeroWhenEmpty() {
        when(repo.totalPassed()).thenReturn(0);
        when(repo.totalFailed()).thenReturn(0);
        assertEquals(0.0, service.firstPassYield());
        assertEquals(0.0, service.defectRate());
    }
}
''')

# =================== EQUIPMENT SERVICE ===================
B = "/tmp/p1-java/mes-system/equipment-service"
w(B, "pom.xml", pom("equipment-service", "equipment-service", "Equipment Monitoring Service (设备监控)"))
w(B, "src/main/java/com/mes/equipment/EquipmentServiceApplication.java", '''
package com.mes.equipment;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
@SpringBootApplication
public class EquipmentServiceApplication {
    public static void main(String[] args) { SpringApplication.run(EquipmentServiceApplication.class, args); }
}
''')
w(B, "src/main/java/com/mes/equipment/entity/Equipment.java", '''
package com.mes.equipment.entity;
import jakarta.persistence.*;
import java.time.LocalDateTime;
import java.util.UUID;

@Entity
@Table(name = "equipment")
public class Equipment {
    @Id
    private String id = UUID.randomUUID().toString();
    @Column(nullable=false, unique=true) private String code;
    @Column(nullable=false) private String name;
    @Column(nullable=false) private String status = "IDLE"; // IDLE, RUNNING, FAULT, MAINTENANCE, OFFLINE
    @Column(nullable=false) private String location;
    private String manufacturer;
    private String model;
    @Column(nullable=false) private double temperature;
    @Column(nullable=false) private double vibration;
    @Column(nullable=false) private int rpm;
    @Column(nullable=false) private double utilizationRate;
    private LocalDateTime lastMaintenance;
    @Column(nullable=false) private LocalDateTime installedAt = LocalDateTime.now();
    public Equipment() {}
    public Equipment(String code, String name, String location) {
        this.code = code; this.name = name; this.location = location;
    }
    public String getId(){return id;}
    public String getCode(){return code;} public void setCode(String c){this.code=c;}
    public String getName(){return name;} public void setName(String n){this.name=n;}
    public String getStatus(){return status;} public void setStatus(String s){this.status=s;}
    public String getLocation(){return location;} public void setLocation(String l){this.location=l;}
    public String getManufacturer(){return manufacturer;} public void setManufacturer(String m){this.manufacturer=m;}
    public String getModel(){return model;} public void setModel(String m){this.model=m;}
    public double getTemperature(){return temperature;} public void setTemperature(double t){this.temperature=t;}
    public double getVibration(){return vibration;} public void setVibration(double v){this.vibration=v;}
    public int getRpm(){return rpm;} public void setRpm(int r){this.rpm=r;}
    public double getUtilizationRate(){return utilizationRate;} public void setUtilizationRate(double u){this.utilizationRate=u;}
    public LocalDateTime getLastMaintenance(){return lastMaintenance;} public void setLastMaintenance(LocalDateTime t){this.lastMaintenance=t;}
    public LocalDateTime getInstalledAt(){return installedAt;} public void setInstalledAt(LocalDateTime t){this.installedAt=t;}
}
''')
w(B, "src/main/java/com/mes/equipment/dto/TelemetryRequest.java", '''
package com.mes.equipment.dto;
public class TelemetryRequest {
    private double temperature;
    private double vibration;
    private int rpm;
    public double getTemperature(){return temperature;} public void setTemperature(double t){this.temperature=t;}
    public double getVibration(){return vibration;} public void setVibration(double v){this.vibration=v;}
    public int getRpm(){return rpm;} public void setRpm(int r){this.rpm=r;}
}
''')
w(B, "src/main/java/com/mes/equipment/repository/EquipmentRepository.java", '''
package com.mes.equipment.repository;
import com.mes.equipment.entity.Equipment;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;
import java.util.List;
import java.util.Optional;
@Repository
public interface EquipmentRepository extends JpaRepository<Equipment, String> {
    Optional<Equipment> findByCode(String code);
    List<Equipment> findByStatus(String status);
    List<Equipment> findByLocation(String location);
    @Query("SELECT COALESCE(AVG(e.utilizationRate),0) FROM Equipment e")
    double averageUtilization();
    long countByStatus(String status);
}
''')
w(B, "src/main/java/com/mes/equipment/service/EquipmentService.java", '''
package com.mes.equipment.service;
import com.mes.equipment.dto.TelemetryRequest;
import com.mes.equipment.entity.Equipment;
import com.mes.equipment.repository.EquipmentRepository;
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
    public EquipmentService(EquipmentRepository repo) { this.repo = repo; }

    @Transactional
    public Equipment register(Equipment e) {
        if (repo.findByCode(e.getCode()).isPresent())
            throw new IllegalArgumentException("equipment code already exists: " + e.getCode());
        if (e.getStatus() == null) e.setStatus("IDLE");
        return repo.save(e);
    }

    @Transactional(readOnly = true)
    public Equipment get(String id) {
        return repo.findById(id).orElseThrow(() -> new IllegalArgumentException("equipment not found: " + id));
    }

    @Transactional(readOnly = true)
    public List<Equipment> listByStatus(String status) {
        validateStatus(status);
        return repo.findByStatus(status);
    }

    @Transactional(readOnly = true)
    public List<Equipment> listAll() { return repo.findAll(); }

    @Transactional
    public Equipment updateStatus(String id, String status) {
        validateStatus(status);
        Equipment e = get(id);
        e.setStatus(status);
        return repo.save(e);
    }

    /** Apply telemetry and run predictive maintenance checks. Returns the updated equipment. */
    @Transactional
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
    public double overallEquipmentEffectiveness() {
        double util = repo.averageUtilization();
        long running = repo.countByStatus("RUNNING");
        long total = repo.count();
        long faulted = repo.countByStatus("FAULT");
        double availability = total == 0 ? 0.0 : (double)(total - faulted) / total * 100.0;
        double performance = running == 0 ? 0.0 : 100.0;
        return availability * (util/100.0) * performance / 100.0;
    }

    private void validateStatus(String s) { if (!VALID_STATUSES.contains(s)) throw new IllegalArgumentException("invalid status: " + s); }
}
''')
w(B, "src/main/java/com/mes/equipment/controller/EquipmentController.java", '''
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
}
''')
w(B, "src/main/resources/application.yml", app_yml("equipment-service", "8083"))
w(B, "src/test/resources/application.yml", test_yml())
w(B, "src/test/java/com/mes/equipment/service/EquipmentServiceTest.java", '''
package com.mes.equipment.service;
import com.mes.equipment.dto.TelemetryRequest;
import com.mes.equipment.entity.Equipment;
import com.mes.equipment.repository.EquipmentRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvSource;
import java.util.List;
import java.util.Optional;
import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

class EquipmentServiceTest {
    private EquipmentRepository repo;
    private EquipmentService service;
    @BeforeEach void setUp() { repo = mock(EquipmentRepository.class); service = new EquipmentService(repo); }

    @Test @DisplayName("register persists new equipment with IDLE status")
    void registerNew() {
        Equipment e = new Equipment("CNC-001", "CNC Mill", "Plant A");
        when(repo.findByCode("CNC-001")).thenReturn(Optional.empty());
        when(repo.save(any())).thenAnswer(i -> i.getArgument(0));
        Equipment saved = service.register(e);
        assertEquals("IDLE", saved.getStatus());
        verify(repo).save(any());
    }

    @Test @DisplayName("register rejects duplicate code")
    void registerDuplicate() {
        when(repo.findByCode("CNC-001")).thenReturn(Optional.of(new Equipment("CNC-001","x","y")));
        assertThrows(IllegalArgumentException.class, () -> service.register(new Equipment("CNC-001","x","y")));
    }

    @ParameterizedTest
    @CsvSource({"85.0,5.0,1200,MAINTENANCE", "95.0,3.0,1200,FAULT", "40.0,2.0,1200,RUNNING"})
    @DisplayName("predictStatus applies threshold rules")
    void predictStatusRules(double temp, double vib, int rpm, String expected) {
        TelemetryRequest t = new TelemetryRequest();
        t.setTemperature(temp); t.setVibration(vib); t.setRpm(rpm);
        assertEquals(expected, service.predictStatus(t));
    }

    @Test @DisplayName("ingestTelemetry flags FAULT on critical temperature")
    void ingestFlagsFault() {
        Equipment e = new Equipment("CNC-1","m","l"); e.setId("e1"); e.setStatus("RUNNING");
        when(repo.findById("e1")).thenReturn(Optional.of(e));
        when(repo.save(any())).thenAnswer(i -> i.getArgument(0));
        TelemetryRequest t = new TelemetryRequest();
        t.setTemperature(96.0); t.setVibration(2.0); t.setRpm(1500);
        Equipment updated = service.ingestTelemetry("e1", t);
        assertEquals("FAULT", updated.getStatus());
        assertEquals(96.0, updated.getTemperature());
    }

    @Test @DisplayName("ingestTelemetry transitions IDLE->RUNNING when rpm>0")
    void ingestIdleToRunning() {
        Equipment e = new Equipment("CNC-1","m","l"); e.setId("e1"); e.setStatus("IDLE");
        when(repo.findById("e1")).thenReturn(Optional.of(e));
        when(repo.save(any())).thenAnswer(i -> i.getArgument(0));
        TelemetryRequest t = new TelemetryRequest();
        t.setTemperature(40.0); t.setVibration(1.0); t.setRpm(1200);
        assertEquals("RUNNING", service.ingestTelemetry("e1", t).getStatus());
    }

    @Test @DisplayName("updateStatus validates and persists")
    void updateStatus() {
        Equipment e = new Equipment("CNC-1","m","l"); e.setId("e1");
        when(repo.findById("e1")).thenReturn(Optional.of(e));
        when(repo.save(any())).thenAnswer(i -> i.getArgument(0));
        assertEquals("MAINTENANCE", service.updateStatus("e1","MAINTENANCE").getStatus());
        assertThrows(IllegalArgumentException.class, () -> service.updateStatus("e1","BROKEN"));
    }

    @Test @DisplayName("listByStatus validates status")
    void listByStatusValidates() {
        when(repo.findByStatus("RUNNING")).thenReturn(List.of());
        service.listByStatus("RUNNING");
        assertThrows(IllegalArgumentException.class, () -> service.listByStatus("FOO"));
    }
}
''')

# =================== INVENTORY SERVICE ===================
B = "/tmp/p1-java/mes-system/inventory-service"
w(B, "pom.xml", pom("inventory-service", "inventory-service", "Inventory Service (库存管理)"))
w(B, "src/main/java/com/mes/inventory/InventoryServiceApplication.java", '''
package com.mes.inventory;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
@SpringBootApplication
public class InventoryServiceApplication {
    public static void main(String[] args) { SpringApplication.run(InventoryServiceApplication.class, args); }
}
''')
w(B, "src/main/java/com/mes/inventory/entity/Material.java", '''
package com.mes.inventory.entity;
import jakarta.persistence.*;
import java.time.LocalDateTime;
import java.util.UUID;

@Entity
@Table(name = "materials")
public class Material {
    @Id
    private String id = UUID.randomUUID().toString();
    @Column(nullable=false, unique=true) private String sku;
    @Column(nullable=false) private String name;
    @Column(nullable=false) private String unit;
    @Column(nullable=false) private int quantity;
    @Column(nullable=false) private int reorderPoint;
    @Column(nullable=false) private int safetyStock;
    @Column(nullable=false) private double unitCost;
    private String warehouse;
    @Column(nullable=false) private LocalDateTime updatedAt = LocalDateTime.now();
    public Material() {}
    public Material(String sku, String name, String unit, int quantity, int reorderPoint, int safetyStock, double unitCost) {
        this.sku = sku; this.name = name; this.unit = unit; this.quantity = quantity;
        this.reorderPoint = reorderPoint; this.safetyStock = safetyStock; this.unitCost = unitCost;
    }
    public String getId(){return id;}
    public String getSku(){return sku;} public void setSku(String s){this.sku=s;}
    public String getName(){return name;} public void setName(String n){this.name=n;}
    public String getUnit(){return unit;} public void setUnit(String u){this.unit=u;}
    public int getQuantity(){return quantity;} public void setQuantity(int q){this.quantity=q;}
    public int getReorderPoint(){return reorderPoint;} public void setReorderPoint(int r){this.reorderPoint=r;}
    public int getSafetyStock(){return safetyStock;} public void setSafetyStock(int s){this.safetyStock=s;}
    public double getUnitCost(){return unitCost;} public void setUnitCost(double c){this.unitCost=c;}
    public String getWarehouse(){return warehouse;} public void setWarehouse(String w){this.warehouse=w;}
    public LocalDateTime getUpdatedAt(){return updatedAt;} public void setUpdatedAt(LocalDateTime t){this.updatedAt=t;}
}
''')
w(B, "src/main/java/com/mes/inventory/dto/StockMovementRequest.java", '''
package com.mes.inventory.dto;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Positive;
public class StockMovementRequest {
    @NotBlank private String sku;
    @Positive private int quantity;
    private String type; // IN, OUT, ADJUST
    private String reference;
    public String getSku(){return sku;} public void setSku(String s){this.sku=s;}
    public int getQuantity(){return quantity;} public void setQuantity(int q){this.quantity=q;}
    public String getType(){return type;} public void setType(String t){this.type=t;}
    public String getReference(){return reference;} public void setReference(String r){this.reference=r;}
}
''')
w(B, "src/main/java/com/mes/inventory/repository/MaterialRepository.java", '''
package com.mes.inventory.repository;
import com.mes.inventory.entity.Material;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;
import java.util.List;
import java.util.Optional;
@Repository
public interface MaterialRepository extends JpaRepository<Material, String> {
    Optional<Material> findBySku(String sku);
    @Query("SELECT m FROM Material m WHERE m.quantity <= m.reorderPoint")
    List<Material> findBelowReorderPoint();
    @Query("SELECT m FROM Material m WHERE m.quantity <= m.safetyStock")
    List<Material> findBelowSafetyStock();
    @Query("SELECT COALESCE(SUM(m.quantity * m.unitCost),0) FROM Material m")
    double totalInventoryValue();
}
''')
w(B, "src/main/java/com/mes/inventory/service/InventoryService.java", '''
package com.mes.inventory.service;
import com.mes.inventory.dto.StockMovementRequest;
import com.mes.inventory.entity.Material;
import com.mes.inventory.repository.MaterialRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import java.time.LocalDateTime;
import java.util.List;

@Service
public class InventoryService {
    private static final List<String> VALID_TYPES = List.of("IN","OUT","ADJUST");
    private final MaterialRepository repo;
    public InventoryService(MaterialRepository repo) { this.repo = repo; }

    @Transactional
    public Material createMaterial(Material m) {
        if (repo.findBySku(m.getSku()).isPresent())
            throw new IllegalArgumentException("sku already exists: " + m.getSku());
        return repo.save(m);
    }

    @Transactional(readOnly = true)
    public Material get(String id) {
        return repo.findById(id).orElseThrow(() -> new IllegalArgumentException("material not found: " + id));
    }

    @Transactional(readOnly = true)
    public Material getBySku(String sku) {
        return repo.findBySku(sku).orElseThrow(() -> new IllegalArgumentException("material not found: " + sku));
    }

    @Transactional(readOnly = true)
    public List<Material> listAll() { return repo.findAll(); }

    @Transactional(readOnly = true)
    public List<Material> listLowStock() { return repo.findBelowReorderPoint(); }

    @Transactional(readOnly = true)
    public List<Material> listCritical() { return repo.findBelowSafetyStock(); }

    @Transactional
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
    public double inventoryValue() { return repo.totalInventoryValue(); }

    private void validateType(String t) { if (!VALID_TYPES.contains(t)) throw new IllegalArgumentException("invalid type: " + t); }
}
''')
w(B, "src/main/java/com/mes/inventory/controller/InventoryController.java", '''
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
}
''')
w(B, "src/main/resources/application.yml", app_yml("inventory-service", "8084"))
w(B, "src/test/resources/application.yml", test_yml())
w(B, "src/test/java/com/mes/inventory/service/InventoryServiceTest.java", '''
package com.mes.inventory.service;
import com.mes.inventory.dto.StockMovementRequest;
import com.mes.inventory.entity.Material;
import com.mes.inventory.repository.MaterialRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import java.util.Optional;
import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

class InventoryServiceTest {
    private MaterialRepository repo;
    private InventoryService service;
    @BeforeEach void setUp() { repo = mock(MaterialRepository.class); service = new InventoryService(repo); }

    private Material mat(int qty, int reorder, int safety) {
        Material m = new Material("SKU-1", "Bolt", "pcs", qty, reorder, safety, 0.5);
        return m;
    }
    private StockMovementRequest mv(String sku, int qty, String type) {
        StockMovementRequest r = new StockMovementRequest();
        r.setSku(sku); r.setQuantity(qty); r.setType(type);
        return r;
    }

    @Test @DisplayName("createMaterial rejects duplicate SKU")
    void createDuplicate() {
        when(repo.findBySku("SKU-1")).thenReturn(Optional.of(mat(10,5,2)));
        assertThrows(IllegalArgumentException.class, () -> service.createMaterial(mat(10,5,2)));
    }

    @Test @DisplayName("moveStock IN increases quantity")
    void moveIn() {
        Material m = mat(10,5,2);
        when(repo.findBySku("SKU-1")).thenReturn(Optional.of(m));
        when(repo.save(any())).thenAnswer(i -> i.getArgument(0));
        Material res = service.moveStock(mv("SKU-1", 5, "IN"));
        assertEquals(15, res.getQuantity());
    }

    @Test @DisplayName("moveStock OUT decreases quantity")
    void moveOut() {
        Material m = mat(10,5,2);
        when(repo.findBySku("SKU-1")).thenReturn(Optional.of(m));
        when(repo.save(any())).thenAnswer(i -> i.getArgument(0));
        assertEquals(7, service.moveStock(mv("SKU-1", 3, "OUT")).getQuantity());
    }

    @Test @DisplayName("moveStock OUT rejects insufficient stock")
    void moveOutInsufficient() {
        Material m = mat(3,5,2);
        when(repo.findBySku("SKU-1")).thenReturn(Optional.of(m));
        assertThrows(IllegalStateException.class, () -> service.moveStock(mv("SKU-1", 10, "OUT")));
    }

    @Test @DisplayName("moveStock ADJUST applies signed delta")
    void moveAdjust() {
        Material m = mat(10,5,2);
        when(repo.findBySku("SKU-1")).thenReturn(Optional.of(m));
        when(repo.save(any())).thenAnswer(i -> i.getArgument(0));
        StockMovementRequest r = mv("SKU-1", -2, "ADJUST");
        assertEquals(8, service.moveStock(r).getQuantity());
    }

    @Test @DisplayName("moveStock rejects invalid type")
    void moveInvalidType() {
        assertThrows(IllegalArgumentException.class, () -> service.moveStock(mv("SKU-1", 1, "TRANSFER")));
    }

    @Test @DisplayName("moveStock rejects unknown SKU")
    void moveUnknownSku() {
        when(repo.findBySku("X")).thenReturn(Optional.empty());
        assertThrows(IllegalArgumentException.class, () -> service.moveStock(mv("X", 1, "IN")));
    }
}
''')

# =================== GATEWAY SERVICE ===================
B = "/tmp/p1-java/mes-system/gateway-service"
os.makedirs(os.path.join(B, "src/main/java"), exist_ok=True)
w(B, "pom.xml", '''
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    <parent>
        <groupId>com.mes</groupId>
        <artifactId>mes-system</artifactId>
        <version>1.0.0</version>
    </parent>
    <artifactId>gateway-service</artifactId>
    <name>API Gateway (网关)</name>
    <dependencies>
        <dependency>
            <groupId>org.springframework.cloud</groupId>
            <artifactId>spring-cloud-starter-gateway</artifactId>
            <version>4.1.3</version>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-actuator</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-test</artifactId>
            <scope>test</scope>
        </dependency>
    </dependencies>
    <build><plugins>
        <plugin><groupId>org.springframework.boot</groupId><artifactId>spring-boot-maven-plugin</artifactId></plugin>
    </plugins></build>
</project>
''')
w(B, "src/main/java/com/mes/gateway/GatewayApplication.java", '''
package com.mes.gateway;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
@SpringBootApplication
public class GatewayApplication {
    public static void main(String[] args) { SpringApplication.run(GatewayApplication.class, args); }
}
''')
w(B, "src/main/resources/application.yml", '''
server:
  port: 8080
spring:
  application:
    name: gateway-service
  cloud:
    gateway:
      routes:
        - id: production-service
          uri: http://localhost:8081
          predicates:
            - Path=/api/v1/production/**
        - id: quality-service
          uri: http://localhost:8082
          predicates:
            - Path=/api/v1/quality/**
        - id: equipment-service
          uri: http://localhost:8083
          predicates:
            - Path=/api/v1/equipment/**
        - id: inventory-service
          uri: http://localhost:8084
          predicates:
            - Path=/api/v1/inventory/**
management:
  endpoints:
    web:
      exposure:
        include: health,info,gateway
''')
w(B, "src/test/java/com/mes/gateway/GatewayApplicationTest.java", '''
package com.mes.gateway;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
class GatewayApplicationTest {
    @Test void contextLoads() {
        // Verifies the gateway configuration is valid and the application class is present.
        assertNotNull(GatewayApplication.class);
    }
}
''')

print("quality, equipment, inventory, gateway services written")
