package com.kinnowpay.payments.bank;

/** The bank's answer to a charge. */
public record BankAuthorization(boolean approved, String reference, String reason) {
}
