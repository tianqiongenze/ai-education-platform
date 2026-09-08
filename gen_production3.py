#!/usr/bin/env python3
"""Generate remaining production-service files: controller, config, tests, resources."""
import os, textwrap
BASE = "/tmp/p1-java/mes-system/production-service"
def w(rel, content):
    p = os.path.join(BASE, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w") as f:
        f.write(textwrap.dedent(content).lstrip("\n"))

# Controller
w("src/main/java/com/mes/production/controller/ProductionController.java", '''
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
}
''')

# Global exception handler
w("src/main/java/com/mes/production/config/GlobalExceptionHandler.java", '''
package com.mes.production.config;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import java.util.Map;

@RestControllerAdvice
public class GlobalExceptionHandler {
    @ExceptionHandler(IllegalArgumentException.class)
    public ResponseEntity<Map<String,String>> badRequest(IllegalArgumentException e) {
        return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(Map.of("error", e.getMessage()));
    }
    @ExceptionHandler(IllegalStateException.class)
    public ResponseEntity<Map<String,String>> conflict(IllegalStateException e) {
        return ResponseEntity.status(HttpStatus.CONFLICT).body(Map.of("error", e.getMessage()));
    }
}
''')

# application.yml (test uses H2, main uses H2 file so it works without external DB)
w("src/main/resources/application.yml", '''
server:
  port: 8081
spring:
  application:
    name: production-service
  datasource:
    url: jdbc:h2:mem:mesdb;DB_CLOSE_DELAY=-1
    driver-class-name: org.h2.Driver
    username: sa
    password: ""
  jpa:
    hibernate:
      ddl-auto: update
    show-sql: false
    properties:
      hibernate.format_sql: true
  h2:
    console:
      enabled: true
      path: /h2-console
management:
  endpoints:
    web:
      exposure:
        include: health,info,metrics
''')

w("src/test/resources/application.yml", '''
spring:
  datasource:
    url: jdbc:h2:mem:testdb;DB_CLOSE_DELAY=-1;MODE=LEGACY
    driver-class-name: org.h2.Driver
    username: sa
    password: ""
  jpa:
    hibernate:
      ddl-auto: create-drop
''')

# --- TESTS (TDD) ---
# Unit test for the service using a mock repository (no Spring context) -> fast, deterministic
w("src/test/java/com/mes/production/service/ProductionServiceTest.java", '''
package com.mes.production.service;

import com.mes.production.dto.ProductionOrderRequest;
import com.mes.production.dto.ProductionOrderResponse;
import com.mes.production.entity.ProductionOrder;
import com.mes.production.repository.ProductionOrderRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;

import java.util.List;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

class ProductionServiceTest {

    private ProductionOrderRepository repo;
    private ProductionService service;

    @BeforeEach
    void setUp() {
        repo = mock(ProductionOrderRepository.class);
        service = new ProductionService(repo);
    }

    private ProductionOrderRequest req(String product, int qty, String priority) {
        ProductionOrderRequest r = new ProductionOrderRequest();
        r.setProductCode(product);
        r.setQuantity(qty);
        r.setPriority(priority);
        r.setWorkCenter("WC-1");
        return r;
    }

    @Test
    @DisplayName("createOrder persists a CREATED order and returns its data")
    void createOrderPersistsCreatedOrder() {
        when(repo.save(any(ProductionOrder.class))).thenAnswer(inv -> inv.getArgument(0));
        ProductionOrderResponse r = service.createOrder(req("P-A100", 100, "HIGH"));
        assertNotNull(r.id());
        assertEquals("P-A100", r.productCode());
        assertEquals(100, r.quantity());
        assertEquals("CREATED", r.status());
        assertEquals("HIGH", r.priority());
        assertEquals(0, r.completedQuantity());
        verify(repo).save(any(ProductionOrder.class));
    }

    @ParameterizedTest
    @ValueSource(strings = {"LOW", "NORMAL", "HIGH", "URGENT"})
    @DisplayName("createOrder accepts all valid priorities")
    void acceptsValidPriorities(String priority) {
        when(repo.save(any())).thenAnswer(i -> i.getArgument(0));
        assertEquals(priority, service.createOrder(req("P", 1, priority)).priority());
    }

    @Test
    @DisplayName("createOrder rejects invalid priority")
    void rejectsInvalidPriority() {
        assertThrows(IllegalArgumentException.class, () -> service.createOrder(req("P", 10, "CRITICAL")));
    }

    @Test
    @DisplayName("createOrder rejects non-positive quantity")
    void rejectsNonPositiveQuantity() {
        assertThrows(IllegalArgumentException.class, () -> service.createOrder(req("P", 0, "NORMAL")));
        assertThrows(IllegalArgumentException.class, () -> service.createOrder(req("P", -5, "NORMAL")));
    }

    @Test
    @DisplayName("getOrder throws when not found")
    void getOrderThrowsWhenMissing() {
        when(repo.findById("X")).thenReturn(Optional.empty());
        assertThrows(IllegalArgumentException.class, () -> service.getOrder("X"));
    }

    @Nested
    @DisplayName("startProduction lifecycle")
    class StartProduction {
        @Test
        void startsCreatedOrder() {
            ProductionOrder o = new ProductionOrder("P", 50, "NORMAL");
            o.setId("ord-1");
            when(repo.findById("ord-1")).thenReturn(Optional.of(o));
            when(repo.save(any())).thenAnswer(i -> i.getArgument(0));
            ProductionOrderResponse r = service.startProduction("ord-1");
            assertEquals("IN_PROGRESS", r.status());
            assertNotNull(r.actualStart());
        }
        @Test
        void cannotStartAlreadyInProgress() {
            ProductionOrder o = new ProductionOrder("P", 50, "NORMAL");
            o.setStatus("IN_PROGRESS");
            when(repo.findById("ord-2")).thenReturn(Optional.of(o));
            assertThrows(IllegalStateException.class, () -> service.startProduction("ord-2"));
        }
    }

    @Nested
    @DisplayName("reportProgress lifecycle")
    class ReportProgress {
        @Test
        void accumulatesProgressAndAutoCompletes() {
            ProductionOrder o = new ProductionOrder("P", 100, "NORMAL");
            o.setId("ord-3");
            o.setStatus("IN_PROGRESS");
            when(repo.findById("ord-3")).thenReturn(Optional.of(o));
            when(repo.save(any())).thenAnswer(i -> i.getArgument(0));
            // first batch: 60 good, 2 bad
            ProductionOrderResponse r1 = service.reportProgress("ord-3", 60, 2);
            assertEquals(60, r1.completedQuantity());
            assertEquals(2, r1.defectCount());
            assertEquals("IN_PROGRESS", r1.status());
            // second batch: 40 good -> reaches quantity -> COMPLETED
            ProductionOrderResponse r2 = service.reportProgress("ord-3", 40, 0);
            assertEquals(100, r2.completedQuantity());
            assertEquals("COMPLETED", r2.status());
            assertNotNull(r2.actualEnd());
        }
        @Test
        void rejectsProgressOnCreatedOrder() {
            ProductionOrder o = new ProductionOrder("P", 10, "NORMAL");
            when(repo.findById("x")).thenReturn(Optional.of(o));
            assertThrows(IllegalStateException.class, () -> service.reportProgress("x", 5, 0));
        }
        @Test
        void rejectsNegativeProgress() {
            ProductionOrder o = new ProductionOrder("P", 10, "NORMAL");
            o.setStatus("IN_PROGRESS");
            when(repo.findById("x")).thenReturn(Optional.of(o));
            assertThrows(IllegalArgumentException.class, () -> service.reportProgress("x", -1, 0));
            assertThrows(IllegalArgumentException.class, () -> service.reportProgress("x", 0, -1));
        }
    }

    @Nested
    @DisplayName("cancelOrder lifecycle")
    class CancelOrder {
        @Test
        void cancelsInProgressOrder() {
            ProductionOrder o = new ProductionOrder("P", 10, "NORMAL");
            o.setStatus("IN_PROGRESS");
            when(repo.findById("c")).thenReturn(Optional.of(o));
            when(repo.save(any())).thenAnswer(i -> i.getArgument(0));
            assertEquals("CANCELLED", service.cancelOrder("c").status());
        }
        @Test
        void cannotCancelCompletedOrder() {
            ProductionOrder o = new ProductionOrder("P", 10, "NORMAL");
            o.setStatus("COMPLETED");
            when(repo.findById("c")).thenReturn(Optional.of(o));
            assertThrows(IllegalStateException.class, () -> service.cancelOrder("c"));
        }
    }

    @Test
    @DisplayName("calculateYieldRate returns 0 when nothing completed")
    void yieldRateZeroWhenEmpty() {
        when(repo.totalQuantityByStatus("COMPLETED")).thenReturn(0);
        when(repo.totalDefects()).thenReturn(0);
        assertEquals(0.0, service.calculateYieldRate());
    }

    @Test
    @DisplayName("calculateYieldRate computes (completed-defects)/completed*100")
    void yieldRateComputation() {
        when(repo.totalQuantityByStatus("COMPLETED")).thenReturn(100);
        when(repo.totalDefects()).thenReturn(5);
        assertEquals(95.0, service.calculateYieldRate(), 0.0001);
    }

    @Test
    @DisplayName("listByStatus validates status and delegates to repo")
    void listByStatusDelegates() {
        ProductionOrder o = new ProductionOrder("P", 1, "NORMAL");
        o.setStatus("CREATED");
        when(repo.findByStatus("CREATED")).thenReturn(List.of(o));
        List<ProductionOrderResponse> res = service.listByStatus("CREATED");
        assertEquals(1, res.size());
        assertEquals("CREATED", res.get(0).status());
    }

    @Test
    @DisplayName("listByStatus rejects invalid status")
    void listByStatusRejectsInvalid() {
        assertThrows(IllegalArgumentException.class, () -> service.listByStatus("FOO"));
    }
}
''')

# Integration test with full Spring context + H2
w("src/test/java/com/mes/production/controller/ProductionControllerIT.java", '''
package com.mes.production.controller;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.mes.production.dto.ProductionOrderRequest;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest
@AutoConfigureMockMvc
class ProductionControllerIT {

    @Autowired private MockMvc mvc;
    @Autowired private ObjectMapper json;

    @Test
    void createOrderThenRetrieveIt() throws Exception {
        ProductionOrderRequest req = new ProductionOrderRequest();
        req.setProductCode("P-INT-1");
        req.setQuantity(250);
        req.setPriority("HIGH");
        String body = json.writeValueAsString(req);

        String location = mvc.perform(post("/api/v1/production/orders")
                .contentType(MediaType.APPLICATION_JSON).content(body))
            .andExpect(status().isCreated())
            .andExpect(jsonPath("$.status").value("CREATED"))
            .andExpect(jsonPath("$.quantity").value(250))
            .andReturn().getResponse().getContentAsString();

        String id = json.readTree(location).get("id").asText();

        mvc.perform(get("/api/v1/production/orders/" + id))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.productCode").value("P-INT-1"));

        // start it
        mvc.perform(post("/api/v1/production/orders/" + id + "/start")).andExpect(status().isOk())
            .andExpect(jsonPath("$.status").value("IN_PROGRESS"));

        // report progress to completion
        mvc.perform(post("/api/v1/production/orders/" + id + "/progress").param("completed", "250").param("defects", "3"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.status").value("COMPLETED"));

        // yield-rate metric
        mvc.perform(get("/api/v1/production/orders/metrics/yield-rate"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.unit").value("percent"));
    }

    @Test
    void rejectsInvalidOrder() throws Exception {
        ProductionOrderRequest req = new ProductionOrderRequest();
        req.setProductCode("");
        req.setQuantity(0);
        mvc.perform(post("/api/v1/production/orders").contentType(MediaType.APPLICATION_JSON)
                .content(json.writeValueAsString(req)))
            .andExpect(status().isBadRequest());
    }
}
''')

print("production controller/config/tests/resources written")
