# Draft limitations paragraph

Our results describe a stochastic, discrete-time model on synthetic WS, BA,
and degree-matched ER networks, not observed contact networks or forecasts for
real populations. The estimated social cost counts cautious contact reduction
in edge-days (using mean degree and q = 0.8), rather than measured mobility or
economic losses. Broadcast is triggered at a fixed prevalence of 0.02, so
conclusions about repeated on/off responses may change under a different
threshold or adaptive messaging. Detected waves depend on a peak-finding
convention (prominence = max[0.01, 0.2 × peak prevalence], separation of at
least 10 steps); low-amplitude oscillations may not count as separate waves,
and the counted peaks should not be interpreted as independent outbreaks.
Hub-targeted broadcast can reach only the top 10% of nodes by degree in this
implementation: its mean BA final size levels off at 0.944 for budgets at or
above 0.10, whereas uniform broadcast can continue expanding coverage.
Comparisons above that budget therefore do not hold coverage equal. Neither
degree matching across synthetic topologies nor the homogeneous mean-field
SIR comparison validates the model against empirical contact networks, so the
relative rankings and magnitude of benefits need external validation.
