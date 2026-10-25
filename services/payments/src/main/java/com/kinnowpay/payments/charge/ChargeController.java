package com.kinnowpay.payments.charge;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ProblemDetail;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import com.kinnowpay.payments.bank.BankException;
import com.kinnowpay.payments.bank.BankTimeoutException;

import jakarta.validation.Valid;

/** The HTTP endpoints for charges. */
@RestController
@RequestMapping("/charges")
public class ChargeController {

    private static final Logger log = LoggerFactory.getLogger(ChargeController.class);

    private final ChargeService service;

    public ChargeController(ChargeService service) {
        this.service = service;
    }

    @PostMapping
    public ResponseEntity<ChargeResponse> create(
            @Valid @RequestBody ChargeRequest request,
            @RequestHeader(name = "X-Request-ID", defaultValue = "-") String requestId) {
        Charge charge = service.charge(request, requestId);
        return ResponseEntity.status(HttpStatus.CREATED).body(ChargeResponse.from(charge));
    }

    @GetMapping("/{id}")
    public ResponseEntity<ChargeResponse> get(@PathVariable long id) {
        return service.find(id)
                .map(charge -> ResponseEntity.ok(ChargeResponse.from(charge)))
                .orElseGet(() -> ResponseEntity.notFound().build());
    }

    /** The bank did not answer within the time limit. */
    @ExceptionHandler(BankTimeoutException.class)
    public ProblemDetail bankTimedOut(BankTimeoutException error) {
        log.warn("bank call timed out: {}", error.getMessage());
        return ProblemDetail.forStatusAndDetail(HttpStatus.GATEWAY_TIMEOUT, "the bank did not answer in time");
    }

    /** The bank could not be reached, or answered with an error. */
    @ExceptionHandler(BankException.class)
    public ProblemDetail bankFailed(BankException error) {
        log.warn("bank call failed: {}", error.getMessage());
        return ProblemDetail.forStatusAndDetail(HttpStatus.BAD_GATEWAY, "the bank could not be used");
    }
}
