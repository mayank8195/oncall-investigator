package com.kinnowpay.payments.charge;

import java.util.Optional;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.stereotype.Service;

import com.kinnowpay.payments.bank.BankAuthorization;
import com.kinnowpay.payments.bank.BankClient;

/** Charges an order through the bank and records the outcome. */
@Service
public class ChargeService {

    static final String APPROVED = "approved";
    static final String DECLINED = "declined";

    private static final Logger log = LoggerFactory.getLogger(ChargeService.class);

    private final ChargeRepository charges;
    private final BankClient bank;

    public ChargeService(ChargeRepository charges, BankClient bank) {
        this.charges = charges;
        this.bank = bank;
    }

    /**
     * Charges an order once. A repeated request for the same order returns the first charge and
     * does not call the bank again.
     *
     * <p>The method is deliberately not @Transactional: a transaction would hold a database
     * connection for as long as the bank takes to answer.
     */
    public Charge charge(ChargeRequest request, String requestId) {
        Optional<Charge> existing = charges.findByOrderId(request.orderId());
        if (existing.isPresent()) {
            log.info("charge already exists: order_id={} request_id={}", request.orderId(), requestId);
            return existing.get();
        }

        BankAuthorization authorization = bank.authorize(
                request.amountPaise(), request.cardNumber(), request.merchantId(), requestId);

        Charge charge = new Charge(
                request.orderId(),
                request.amountPaise(),
                request.cardNumber(),
                request.merchantId(),
                authorization.approved() ? APPROVED : DECLINED,
                authorization.reference());
        try {
            charge = charges.save(charge);
        } catch (DataIntegrityViolationException duplicate) {
            // Another request charged the same order between our check and our save
            return charges.findByOrderId(request.orderId()).orElseThrow(() -> duplicate);
        }
        log.info("charge recorded: order_id={} status={} request_id={}",
                charge.getOrderId(), charge.getStatus(), requestId);
        return charge;
    }

    public Optional<Charge> find(long id) {
        return charges.findById(id);
    }
}
