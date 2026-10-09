package com.kinnowpay.payments.bank;

import java.net.SocketTimeoutException;
import java.time.Duration;
import java.util.Map;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestClientResponseException;

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
     * @throws BankTimeoutException if the bank does not answer in time
     * @throws BankException if the bank cannot be reached or returns an error
     */
    public BankAuthorization authorize(long amountPaise, String cardNumber, String merchantId, String requestId) {
        // The bank's JSON is snake_case, so the body is built by hand
        Map<String, Object> body = Map.of(
                "amount_paise", amountPaise,
                "card_number", cardNumber,
                "merchant_id", merchantId);
        try {
            return restClient.post()
                    .uri("/authorize")
                    .contentType(MediaType.APPLICATION_JSON)
                    .header("X-Request-ID", requestId)
                    .body(body)
                    .retrieve()
                    .body(BankAuthorization.class);
        } catch (RestClientResponseException error) {
            throw new BankException("the bank answered " + error.getStatusCode().value(), error);
        } catch (RestClientException error) {
            if (causedByTimeout(error)) {
                throw new BankTimeoutException("the bank did not answer in time", error);
            }
            throw new BankException("the bank could not be reached", error);
        }
    }

    /** Spring wraps the timeout in its own exceptions, so look down the chain of causes. */
    private static boolean causedByTimeout(Throwable error) {
        for (Throwable cause = error; cause != null; cause = cause.getCause()) {
            if (cause instanceof SocketTimeoutException) {
                return true;
            }
        }
        return false;
    }
}
