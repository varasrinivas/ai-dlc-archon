package com.acmehealth.priorauth.aging;

import org.junit.jupiter.api.Test;

import java.time.LocalDate;
import java.util.Set;

import static org.assertj.core.api.Assertions.assertThat;

class AgeBadgeTest {

    @Test // FR2: over the limit means strictly more than the threshold; 5 is not flagged, 6 is
    void flagOnlyWhenOverTheThreshold() {
        LocalDate mon5 = LocalDate.of(2026, 10, 5);
        AgeBadge five = AgeBadge.of(mon5, LocalDate.of(2026, 10, 12), Set.of(), 5);   // Tue..Mon = 5 bd
        AgeBadge six = AgeBadge.of(mon5, LocalDate.of(2026, 10, 13), Set.of(), 5);    // ..Tue = 6 bd
        assertThat(five.overLimit()).isFalse();
        assertThat(five.label()).isEqualTo("5 bd");
        assertThat(six.overLimit()).isTrue();
        assertThat(six.label()).isEqualTo("6 bd OVER 5");
    }
}
