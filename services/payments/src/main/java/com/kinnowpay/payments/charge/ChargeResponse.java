package com.kinnowpay.payments.charge;

/** The JSON returned for a charge. The card number is deliberately left out. */
public record ChargeResponse(Long id, long orderId, long amountPaise, String status, String bankReference) {

    static ChargeResponse from(Charge charge) {
        return new ChargeResponse(
                charge.getId(),
                charge.getOrderId(),
                charge.getAmountPaise(),
                charge.getStatus(),
                charge.getBankReference());
    }
}
