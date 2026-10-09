package com.kinnowpay.payments.charge;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Positive;

/** The JSON body of POST /charges. Arrives as snake_case: order_id, amount_paise and so on. */
public record ChargeRequest(
        @NotNull @Positive Long orderId,
        @NotNull @Positive Long amountPaise,
        @NotBlank @Pattern(regexp = "\\d{12,19}") String cardNumber,
        @NotBlank String merchantId) {
}
