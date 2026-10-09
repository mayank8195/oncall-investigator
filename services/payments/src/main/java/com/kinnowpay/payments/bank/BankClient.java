package com.kinnowpay.payments.bank;

import java.time.Duration;
import java.util.Map;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;

/** Calls the external bank's API, with a time limit on connecting and on waiting for the answer. */
@Component
public class BankClient {

    private final RestClient restClient;

    public BankClient(
            @Value("${bank.base-url}") String baseUrl,
            @Value("${bank.connect-timeout-ms}") int connectTimeoutMs,
            @Value("${bank.read-timeout-ms}") int readTimeoutMs) {
        var requestFactory = new SimpleClientHttpRequestFactory();
        requestFactory.setConnectTimeout(Duration.ofMillis(connectTimeoutMs));
        requestFactory.setReadTimeout(Duration.ofMillis(readTimeoutMs));
        this.restClient = RestClient.builder()
                .baseUrl(baseUrl)
                .requestFactory(requestFactory)
                .build();
    }

    /**
     * Asks the bank to authorise a charge.
     *
     * @throws org.springframework.web.client.ResourceAccessException if the bank cannot be reached
     *     or does not answer in time
     */
    public BankAuthorization authorize(long amountPaise, String cardNumber, String merchantId, String requestId) {
        // The bank's JSON is snake_case, so the body is built by hand
        Map<String, Object> body = Map.of(
                "amount_paise", amountPaise,
                "card_number", cardNumber,
                "merchant_id", merchantId);
        return restClient.post()
                .uri("/authorize")
                .contentType(MediaType.APPLICATION_JSON)
                .header("X-Request-ID", requestId)
                .body(body)
                .retrieve()
                .body(BankAuthorization.class);
    }
}
