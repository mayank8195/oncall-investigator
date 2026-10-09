package com.kinnowpay.payments.charge;

import java.util.Optional;

import org.springframework.data.jpa.repository.JpaRepository;

/** Database access for charges. Spring writes the implementation from the method names. */
public interface ChargeRepository extends JpaRepository<Charge, Long> {

    Optional<Charge> findByOrderId(long orderId);
}
