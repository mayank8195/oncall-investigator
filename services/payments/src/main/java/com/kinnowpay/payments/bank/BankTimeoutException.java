package com.kinnowpay.payments.bank;

/** The bank did not answer within the time limit. */
public class BankTimeoutException extends BankException {

    public BankTimeoutException(String message, Throwable cause) {
        super(message, cause);
    }
}
