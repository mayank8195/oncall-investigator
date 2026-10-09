package com.kinnowpay.payments.charge;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import java.util.Optional;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.http.MediaType;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.web.client.ResourceAccessException;

/** Tests the HTTP layer alone: JSON in, status codes and JSON out. No database, no bank. */
@WebMvcTest(ChargeController.class)
class ChargeControllerTest {

    private static final String VALID_BODY = """
            {"order_id": 42, "amount_paise": 99800, "card_number": "4111111111111111", "merchant_id": "MRC000001"}
            """;

    @Autowired
    private MockMvc mvc;

    @MockitoBean
    private ChargeService service;

    @Test
    void aValidChargeReturns201WithoutTheCardNumber() throws Exception {
        when(service.charge(any(ChargeRequest.class), eq("req-1")))
                .thenReturn(new Charge(42L, 99800L, "4111111111111111", "MRC000001", "approved", "BNK-1"));

        mvc.perform(post("/charges")
                        .contentType(MediaType.APPLICATION_JSON)
                        .header("X-Request-ID", "req-1")
                        .content(VALID_BODY))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.order_id").value(42))
                .andExpect(jsonPath("$.status").value("approved"))
                .andExpect(jsonPath("$.bank_reference").value("BNK-1"))
                .andExpect(jsonPath("$.card_number").doesNotExist());
    }

    @Test
    void aMalformedCardNumberIsRejectedWith400() throws Exception {
        mvc.perform(post("/charges")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {"order_id": 42, "amount_paise": 99800, "card_number": "abc", "merchant_id": "MRC000001"}
                                """))
                .andExpect(status().isBadRequest());
    }

    @Test
    void aBankThatDoesNotAnswerBecomes504() throws Exception {
        when(service.charge(any(ChargeRequest.class), any()))
                .thenThrow(new ResourceAccessException("Read timed out"));

        mvc.perform(post("/charges").contentType(MediaType.APPLICATION_JSON).content(VALID_BODY))
                .andExpect(status().isGatewayTimeout());
    }

    @Test
    void anUnknownChargeIs404() throws Exception {
        when(service.find(7L)).thenReturn(Optional.empty());

        mvc.perform(get("/charges/7")).andExpect(status().isNotFound());
    }
}
