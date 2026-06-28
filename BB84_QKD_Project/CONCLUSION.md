# Project Conclusion

This project demonstrates the BB84 Quantum Key Distribution protocol from the ideal case to realistic noisy and attacked scenarios.

In a noise-free channel, Alice and Bob obtain matching sifted keys after basis reconciliation, producing QBER close to zero. With bit-flip, phase-flip, depolarizing, and amplitude-damping noise, QBER increases and the usable key rate decreases. This shows why QBER is one of the most important measurements in QKD security analysis.

The Eve attack notebooks show that intercept-resend eavesdropping introduces detectable disturbance. When Eve is combined with channel noise, the total QBER can cross an abort threshold, meaning Alice and Bob should reject the key or investigate the channel.

Information reconciliation can reduce mismatches, but it leaks some information through public communication. Privacy amplification solves this by compressing the reconciled key into a shorter and more secure final key.

Overall, BB84 is secure because quantum measurement disturbance makes eavesdropping visible statistically. The final usable key depends on channel noise, QBER, reconciliation efficiency, and privacy amplification.
