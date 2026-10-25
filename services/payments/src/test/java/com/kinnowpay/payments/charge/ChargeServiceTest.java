package com.kinnowpay.payments.charge;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyLong;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import java.util.Optional;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.dao.DataIntegrityViolationException;

import com.kinnowpay.payments.bank.BankAuthorization;
import com.kinnowpay.payments.bank.BankClient;

/** Tests the charging rules with the database and the bank replaced by mocks. */
@ExtendWith(MockitoExtension.class)
class ChargeServiceTest {

    private static final ChargeRequest REQUEST = new ChargeRequest(42L, 99800L, "4111111111111111", "MRC000001");

    @Mock
    private ChargeRepository charges;

    @Mock
    private BankClient bank;

    @InjectMocks
    private ChargeService service;

    @Test
    void approvedByTheBankIsRecordedAsApproved() {
        when(charges.findByOrderId(42L)).thenReturn(Optional.empty());
        when(bank.authorize(99800L, "4111111111111111", "MRC000001", "req-1"))
                .thenReturn(new BankAuthorization(true, "BNK-1", null));
        when(charges.save(any(Charge.class))).thenAnswer(call -> call.getArgument(0));

        Charge charge = service.charge(REQUEST, "req-1");

        assertThat(charge.getStatus()).isEqualTo("approved");
        assertThat(charge.getBankReference()).isEqualTo("BNK-1");
    }

    @Test
    void declinedByTheBankIsRecordedAsDeclined() {
        when(charges.findByOrderId(42L)).thenReturn(Optional.empty());
        when(bank.authorize(anyLong(), anyString(), anyString(), anyString()))
                .thenReturn(new BankAuthorization(false, "BNK-2", "insufficient_funds"));
        when(charges.save(any(Charge.class))).thenAnswer(call -> call.getArgument(0));

        Charge charge = service.charge(REQUEST, "req-1");

        assertThat(charge.getStatus()).isEqualTo("declined");
    }

    @Test
    void anOrderAlreadyChargedIsNotSentToTheBankAgain() {
        Charge first = new Charge(42L, 99800L, "4111111111111111", "MRC000001", "approved", "BNK-1");
        when(charges.findByOrderId(42L)).thenReturn(Optional.of(first));

        Charge charge = service.charge(REQUEST, "req-2");

        assertThat(charge).isSameAs(first);
        verify(bank, never()).authorize(anyLong(), anyString(), anyString(), anyString());
        verify(charges, never()).save(any(Charge.class));
    }

    @Test
    void losingARaceToAnotherRequestReturnsTheWinnersCharge() {
        Charge winner = new Charge(42L, 99800L, "4111111111111111", "MRC000001", "approved", "BNK-1");
        when(charges.findByOrderId(42L)).thenReturn(Optional.empty(), Optional.of(winner));
        when(bank.authorize(anyLong(), anyString(), anyString(), anyString()))
                .thenReturn(new BankAuthorization(true, "BNK-3", null));
        when(charges.save(any(Charge.class))).thenThrow(new DataIntegrityViolationException("duplicate order_id"));

        Charge charge = service.charge(REQUEST, "req-3");

        assertThat(charge).isSameAs(winner);
    }
}
