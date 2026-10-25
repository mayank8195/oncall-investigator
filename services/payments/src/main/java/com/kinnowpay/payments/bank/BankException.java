package com.kinnowpay.payments.bank;

/** The bank could not give a usable answer: unreachable, or it returned an error. */
public class BankException extends RuntimeException {

    public BankException(String message, Throwable cause) {
        super(message, cause);
    }
}
