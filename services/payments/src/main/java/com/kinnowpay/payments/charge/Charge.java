package com.kinnowpay.payments.charge;

import java.time.Instant;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

/** One row of the charges table. */
@Entity
@Table(name = "charges")
public class Charge {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "order_id", nullable = false, unique = true)
    private long orderId;

    @Column(name = "amount_paise", nullable = false)
    private long amountPaise;

    @Column(name = "card_number", nullable = false)
    private String cardNumber;

    @Column(name = "merchant_id", nullable = false)
    private String merchantId;

    @Column(nullable = false)
    private String status;

    @Column(name = "bank_reference")
    private String bankReference;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt = Instant.now();

    /** JPA needs a constructor with no arguments. */
    protected Charge() {
    }

    public Charge(long orderId, long amountPaise, String cardNumber, String merchantId, String status,
            String bankReference) {
        this.orderId = orderId;
        this.amountPaise = amountPaise;
        this.cardNumber = cardNumber;
        this.merchantId = merchantId;
        this.status = status;
        this.bankReference = bankReference;
    }

    public Long getId() {
        return id;
    }

    public long getOrderId() {
        return orderId;
    }

    public long getAmountPaise() {
        return amountPaise;
    }

    public String getStatus() {
        return status;
    }

    public String getBankReference() {
        return bankReference;
    }
}
