#!/usr/bin/env bash
# Builds a Spring Boot project whose branch wires a bean with @Service and field
# injection, next to a configuration wiring test that rightly uses @Autowired.
set -euo pipefail

git init -q -b main
git config user.name "Eval"
git config user.email "eval@example.com"
B=src/main/java/com/example/billing
T=src/test/java/com/example/billing
mkdir -p $B $T
printf '<project><modelVersion>4.0.0</modelVersion><groupId>com.example</groupId><artifactId>billing</artifactId><version>1</version>\n<parent><groupId>org.springframework.boot</groupId><artifactId>spring-boot-starter-parent</artifactId><version>3.3.5</version></parent></project>\n' > pom.xml
cat > $B/BillingApplication.java <<'EOF'
package com.example.billing;

import org.springframework.boot.autoconfigure.SpringBootApplication;

/** Entry point of the billing service. */
@SpringBootApplication
public class BillingApplication {
}
EOF
git add -A
git commit -q -m "Initial service"

git checkout -q -b invoice-numbers
mkdir -p $B/invoice $T/invoice
cat > $B/invoice/InvoiceNumberGenerator.java <<'EOF'
package com.example.billing.invoice;

/** Generates sequential invoice numbers. */
class InvoiceNumberGenerator {
    private long nextNumber = 1;

    synchronized long nextInvoiceNumber() {
        return nextNumber++;
    }
}
EOF
cat > $B/invoice/InvoiceService.java <<'EOF'
package com.example.billing.invoice;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

/** Issues invoices with their numbers. */
@Service
class InvoiceService {
    @Autowired
    private InvoiceNumberGenerator invoiceNumberGenerator;

    String issueInvoiceNumber() {
        return "INV-" + invoiceNumberGenerator.nextInvoiceNumber();
    }
}
EOF
cat > $T/invoice/InvoiceWiringTest.java <<'EOF'
package com.example.billing.invoice;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

import static org.assertj.core.api.Assertions.assertThat;

/** Checks the invoice beans are wired. */
@SpringBootTest
class InvoiceWiringTest {
    @Autowired
    InvoiceService invoiceService;

    @Test
    void invoiceServiceIsWired() {
        assertThat(invoiceService).isNotNull();
    }
}
EOF
git add -A
git commit -q -m "Add invoice numbers"
